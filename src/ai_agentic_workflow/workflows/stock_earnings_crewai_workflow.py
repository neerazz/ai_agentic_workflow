from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

from crewai import Agent, Task, Crew, Process

from src.ai_agentic_workflow.clients.chatgpt_client import DualModelChatClient
from src.ai_agentic_workflow.clients.perplexity_client import DualModelPerplexityClient
from src.ai_agentic_workflow.automation.open_browser import (
    Site,
    start_persistent_browser,
    run_prompt_in_existing_tab,
    close_browser,
)

logger = logging.getLogger(__name__)


def _extract_json_from_text(text: str) -> dict | list | None:
    import re
    if not text:
        return None
    match = re.search(r"```json\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    try:
        return json.loads(text)
    except Exception:
        return None


def _format_earnings_query_prompt(weeks: int = 3) -> str:
    return (
        "You are a financial research assistant. Return ONLY valid JSON. "
        "Task: List publicly-traded US stocks with upcoming earnings in the next "
        f"{weeks} weeks. Include symbol, company_name, earnings_date (YYYY-MM-DD), and market_cap_category (mid or large). "
        "Return a JSON array of at most 50 items with keys: symbol, company_name, earnings_date, market_cap_category."
    )


def _format_perplexity_bull_prompt(symbol: str, custom_prompt: str | None) -> str:
    base = (
        f"Perform a concise bullish-vs-bearish scenario analysis for {symbol}. "
        "Focus on fundamentals, recent earnings trends, guidance, catalysts, risks. "
        "Return ONLY JSON with keys: symbol, bullish_thesis, key_catalysts, target_price, target_horizon_days, bullish_probability, notes."
    )
    if custom_prompt:
        base += "\nAdditional instructions: " + custom_prompt
    return base


def _format_top2_selection_prompt(perplexity_json_payloads: List[dict]) -> str:
    return (
        "You are screening stocks for near-term bullish potential. You will receive JSON analyses (one per stock).\n"
        "Pick the two strongest bullish candidates using catalysts, probability, and upside.\n"
        "Return ONLY JSON with this schema: {\"picks\":[{\"symbol\":str,\"reason\":str}],\"ranking\":[{\"symbol\":str,\"score\":number}]}.\n"
        f"Analyses: {json.dumps(perplexity_json_payloads)[:12000]}"
    )


def _format_prediction_prompt(symbol: str) -> str:
    return (
        f"For {symbol}, predict a 30-day price target and percentage growth with probability bands.\n"
        "Return ONLY JSON: {symbol, base_case_target, upside_target, downside_target, base_prob, upside_prob, downside_prob, assumptions}."
    )


@dataclass
class StockWorkflowState:
    weeks: int = 3
    desired_count: int = 10
    custom_bull_prompt: str | None = None
    earnings_list: List[dict] = field(default_factory=list)
    perplexity_analyses: Dict[str, dict] = field(default_factory=dict)
    top2: List[str] = field(default_factory=list)
    predictions: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class StockEarningsCrewWorkflow:
    """CrewAI-based workflow to analyze stocks around upcoming earnings."""

    def __init__(self, weeks: int = 3, desired_count: int = 10, custom_bull_prompt: str | None = None, keep_browser_open: bool = False):
        self.state = StockWorkflowState(weeks=weeks, desired_count=desired_count, custom_bull_prompt=custom_bull_prompt)
        self.keep_browser_open = keep_browser_open

        # LLM clients
        self.chat = DualModelChatClient()
        self.pplx_api = DualModelPerplexityClient()

        # Agents
        self.screener = Agent(
            role="Earnings Screener",
            goal="Produce a JSON list of US stocks with earnings in the next N weeks, including market cap category.",
            backstory="An experienced equity research assistant adept at data hygiene and JSON-only outputs.",
            llm=self.chat.get_llm("reasoning"),
        )
        self.selector = Agent(
            role="Bullish Selector",
            goal="Choose the top-2 bullish stocks from multiple analyses.",
            backstory="A portfolio analyst focused on risk-adjusted upside near earnings.",
            llm=self.chat.get_llm("reasoning"),
        )
        self.predictor = Agent(
            role="Price Predictor",
            goal="Provide 30-day price targets and probability bands in strict JSON.",
            backstory="Quantitative analyst estimating scenario distributions.",
            llm=self.chat.get_llm("reasoning"),
        )

    def run(self) -> Dict[str, Any]:
        driver = start_persistent_browser()
        try:
            # Screener task (ChatGPT)
            screener_task = Task(
                description=_format_earnings_query_prompt(self.state.weeks),
                expected_output="JSON array of stocks with fields: symbol, company_name, earnings_date, market_cap_category",
                agent=self.screener,
            )
            crew = Crew(tasks=[screener_task], agents=[self.screener], process=Process.sequential)
            res = crew.kickoff({})
            raw = res.tasks_output[0].raw
            earnings_json = _extract_json_from_text(raw) or []

            # Filter to mid/large and trim
            cleaned: List[dict] = []
            for item in earnings_json:
                symbol = (item.get("symbol") or "").strip().upper()
                cap = (item.get("market_cap_category") or "").strip().lower()
                if not symbol:
                    continue
                if cap not in {"mid", "large"}:
                    continue
                cleaned.append({
                    "symbol": symbol,
                    "company_name": item.get("company_name"),
                    "earnings_date": item.get("earnings_date"),
                    "market_cap_category": cap,
                })
            self.state.earnings_list = cleaned[: self.state.desired_count]

            # Perplexity analyses via browser (fallback to API)
            analyses: Dict[str, dict] = {}
            for row in self.state.earnings_list:
                sym = row["symbol"]
                prompt = _format_perplexity_bull_prompt(sym, self.state.custom_bull_prompt)
                try:
                    _, text = run_prompt_in_existing_tab(driver, Site.PERPLEXITY, prompt, 45)
                    analysis = _extract_json_from_text(text or "") or {}
                    if not analysis:
                        api_resp = self.pplx_api.get_llm("reasoning").invoke(prompt)
                        analysis = _extract_json_from_text(getattr(api_resp, "content", str(api_resp)) or "") or {}
                except Exception as e:
                    logger.warning("Perplexity browser error for %s: %s; using API fallback.", sym, e)
                    api_resp = self.pplx_api.get_llm("reasoning").invoke(prompt)
                    analysis = _extract_json_from_text(getattr(api_resp, "content", str(api_resp)) or "") or {}

                if isinstance(analysis, dict):
                    prob = analysis.get("bullish_probability")
                    if prob is None or (isinstance(prob, (int, float)) and prob >= 0.5):
                        analyses[sym] = analysis
            self.state.perplexity_analyses = analyses
            if not analyses:
                return {
                    "earnings_list": self.state.earnings_list,
                    "perplexity_analyses": analyses,
                    "error": "No bullish candidates found.",
                }

            # Selection task (ChatGPT)
            selection_prompt = _format_top2_selection_prompt(list(analyses.values()))
            selector_task = Task(
                description=selection_prompt,
                expected_output="JSON with keys: picks (2 symbols with reasons), ranking (scored list)",
                agent=self.selector,
            )
            crew = Crew(tasks=[selector_task], agents=[self.selector], process=Process.sequential)
            sel_res = crew.kickoff({})
            sel_json = _extract_json_from_text(sel_res.tasks_output[0].raw) or {}
            top2 = [item.get("symbol") for item in (sel_json.get("picks") or []) if item.get("symbol")][:2]
            self.state.top2 = top2

            # Predictions for top2
            preds: Dict[str, Dict[str, Any]] = {}
            for sym in top2:
                pred_prompt = _format_prediction_prompt(sym)
                # ChatGPT
                pred_task = Task(
                    description=pred_prompt,
                    expected_output="Strict JSON with price targets and probabilities",
                    agent=self.predictor,
                )
                crew = Crew(tasks=[pred_task], agents=[self.predictor], process=Process.sequential)
                pred_res = crew.kickoff({})
                gpt_json = _extract_json_from_text(pred_res.tasks_output[0].raw) or {}

                # Perplexity via browser, fallback to API
                try:
                    _, p_text = run_prompt_in_existing_tab(driver, Site.PERPLEXITY, pred_prompt, 45)
                    pplx_json = _extract_json_from_text(p_text or "") or {}
                    if not pplx_json:
                        p_api = self.pplx_api.get_llm("reasoning").invoke(pred_prompt)
                        pplx_json = _extract_json_from_text(getattr(p_api, "content", str(p_api)) or "") or {}
                except Exception:
                    p_api = self.pplx_api.get_llm("reasoning").invoke(pred_prompt)
                    pplx_json = _extract_json_from_text(getattr(p_api, "content", str(p_api)) or "") or {}

                preds[sym] = {"chatgpt": gpt_json, "perplexity": pplx_json}

            self.state.predictions = preds
            return {
                "earnings_list": self.state.earnings_list,
                "perplexity_analyses": self.state.perplexity_analyses,
                "top2": self.state.top2,
                "predictions": self.state.predictions,
            }
        finally:
            if not self.keep_browser_open:
                try:
                    close_browser(driver)
                except Exception:
                    pass


def run_stock_earnings_crewai_workflow(weeks: int = 3, desired_count: int = 10, custom_bull_prompt: str | None = None, keep_browser_open: bool = False) -> Dict[str, Any]:
    workflow = StockEarningsCrewWorkflow(weeks=weeks, desired_count=desired_count, custom_bull_prompt=custom_bull_prompt, keep_browser_open=keep_browser_open)
    return workflow.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    out = run_stock_earnings_crewai_workflow()
    print(json.dumps(out, indent=2))

