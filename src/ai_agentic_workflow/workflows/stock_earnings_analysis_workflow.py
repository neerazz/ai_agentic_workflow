import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Tuple

from langchain_core.prompts import PromptTemplate

from src.ai_agentic_workflow.clients.chatgpt_client import DualModelChatClient
from src.ai_agentic_workflow.clients.perplexity_client import DualModelPerplexityClient
from src.ai_agentic_workflow.automation.open_browser import (
    Site,
    start_persistent_browser,
    run_prompt_in_existing_tab,
    close_browser,
)

logger = logging.getLogger(__name__)


@dataclass
class StockPick:
    symbol: str
    name: str | None = None
    market_cap_category: str | None = None  # mid, large


def _safe_json_loads(text: str) -> dict | list | None:
    try:
        return json.loads(text)
    except Exception:
        return None


def _extract_json_from_text(text: str) -> dict | list | None:
    if not text:
        return None
    # Try to find a fenced code block with json
    import re
    match = re.search(r"```json\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```", text)
    if match:
        return _safe_json_loads(match.group(1))
    # Fallback: first {...} or [...]
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if match:
        return _safe_json_loads(match.group(1))
    return _safe_json_loads(text)


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


def run_stock_earnings_analysis(
    earnings_weeks: int = 3,
    desired_count: int = 10,
    custom_bull_prompt: str | None = None,
) -> Dict[str, object]:
    """
    End-to-end workflow:
      1) Use ChatGPT to list stocks with earnings in next N weeks
      2) Filter to mid/large cap, top ~desired_count
      3) For each, open Perplexity in browser and get bullish/bearish JSON, keep only bullish
      4) Send all analyses to ChatGPT to pick top 2
      5) For each top 2, query both ChatGPT and Perplexity (browser) for price predictions
    """
    results: Dict[str, object] = {
        "earnings_list": [],
        "perplexity_analyses": {},
        "top2": [],
        "predictions": {},
    }

    chat = DualModelChatClient()
    pplx_api = DualModelPerplexityClient()

    # Start persistent browser once
    driver = start_persistent_browser()
    try:
        # Step 1: Earnings list via ChatGPT (API)
        earnings_prompt = _format_earnings_query_prompt(earnings_weeks)
        earnings_resp = chat.get_llm("reasoning").invoke(earnings_prompt)
        earnings_json = _extract_json_from_text(getattr(earnings_resp, "content", str(earnings_resp))) or []

        # Normalize and filter
        picks: List[StockPick] = []
        for item in earnings_json:
            symbol = (item.get("symbol") or "").strip().upper()
            name = item.get("company_name")
            cap = (item.get("market_cap_category") or "").strip().lower()
            if not symbol:
                continue
            if cap not in {"mid", "large"}:
                continue
            picks.append(StockPick(symbol=symbol, name=name, market_cap_category=cap))
        picks = picks[:desired_count]
        results["earnings_list"] = [p.__dict__ for p in picks]

        # Step 2: Perplexity analyses via browser
        pplx_payloads: Dict[str, dict] = {}
        for p in picks:
            q = _format_perplexity_bull_prompt(p.symbol, custom_bull_prompt)
            try:
                _, text = run_prompt_in_existing_tab(driver, Site.PERPLEXITY, q, 45)
                analysis = _extract_json_from_text(text or "") or {}
                if not analysis:
                    # Fallback to API call if browser failed
                    api_text = pplx_api.get_llm("reasoning").invoke(q)
                    analysis = _extract_json_from_text(getattr(api_text, "content", str(api_text)) or "") or {}
            except Exception as e:
                logger.warning("Perplexity browser error for %s: %s. Falling back to API.", p.symbol, e)
                api_text = pplx_api.get_llm("reasoning").invoke(q)
                analysis = _extract_json_from_text(getattr(api_text, "content", str(api_text)) or "") or {}

            if isinstance(analysis, dict):
                # Only include if probability is numeric and >= 0.5
                prob = analysis.get("bullish_probability")
                if isinstance(prob, (int, float)) and prob >= 0.5:
                    pplx_payloads[p.symbol] = analysis
        results["perplexity_analyses"] = pplx_payloads

        if not pplx_payloads:
            results["error"] = "No bullish candidates found from Perplexity analyses."
            return results

        # Step 3: Select top 2 via ChatGPT
        selection_prompt = _format_top2_selection_prompt(list(pplx_payloads.values()))
        selection_resp = chat.get_llm("reasoning").invoke(selection_prompt)
        selection = _extract_json_from_text(getattr(selection_resp, "content", str(selection_resp))) or {}
        top2 = [item.get("symbol") for item in (selection.get("picks") or []) if item.get("symbol")]
        top2 = top2[:2]
        results["top2"] = top2

        # Step 4: Predictions via both ChatGPT (API) and Perplexity (browser)
        predictions: Dict[str, Dict[str, object]] = {}
        for sym in top2:
            pred_prompt = _format_prediction_prompt(sym)
            # ChatGPT
            gpt_resp = chat.get_llm("reasoning").invoke(pred_prompt)
            gpt_json = _extract_json_from_text(getattr(gpt_resp, "content", str(gpt_resp))) or {}
            # Perplexity via browser, fallback to API
            try:
                _, p_text = run_prompt_in_existing_tab(driver, Site.PERPLEXITY, pred_prompt, 45)
                pplx_json = _extract_json_from_text(p_text or "") or {}
                if not pplx_json:
                    p_api = pplx_api.get_llm("reasoning").invoke(pred_prompt)
                    pplx_json = _extract_json_from_text(getattr(p_api, "content", str(p_api)) or "") or {}
            except Exception:
                p_api = pplx_api.get_llm("reasoning").invoke(pred_prompt)
                pplx_json = _extract_json_from_text(getattr(p_api, "content", str(p_api)) or "") or {}

            predictions[sym] = {"chatgpt": gpt_json, "perplexity": pplx_json}
        results["predictions"] = predictions
        return results

    finally:
        # Keep the browser session open across runs if desired; otherwise close.
        try:
            close_browser(driver)
        except Exception:
            pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    output = run_stock_earnings_analysis(earnings_weeks=3, desired_count=10)
    print(json.dumps(output, indent=2))

