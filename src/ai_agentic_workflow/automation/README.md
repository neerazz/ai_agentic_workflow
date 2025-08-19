# Automation

Utilities for automated web interactions with ChatGPT and Perplexity using Selenium. This module now supports:

- Persistent browser sessions and tab reuse (no repeated logins)
- Reusing the same conversation threads for follow-up prompts
- Cross-service workflows (send result from Service A to Service B, and back to A)
- A ready-made stock earnings analysis workflow

## Requirements

- Python 3.10+
- Selenium, webdriver-manager, Playwright (optional in repo), see `requirements.txt`
- Google Chrome or Chromium installed
  - On Linux, Chromium is fine. On macOS/Windows, Google Chrome is recommended.
  - To override binary detection, set one of the env vars: `CHROME`, `CHROME_BINARY`, or `GOOGLE_CHROME_SHIM` to the Chrome/Chromium binary path.

Ensure all Chrome windows using the target profile are closed before running, otherwise Chrome may refuse to start with that profile.

## Quick Start

```python
from src.ai_agentic_workflow.automation.open_browser import BrowserSessionManager, Site

manager = BrowserSessionManager()  # uses your default Chrome profile to keep you logged in

# 1) Ask ChatGPT
_, r1 = manager.send_and_wait(Site.CHATGPT, "List 5 AI safety principles.")

# 2) Send r1 to Perplexity
_, r2 = manager.send_and_wait(Site.PERPLEXITY, f"Critique these points and add references: {r1}")

# 3) Send r2 back to the SAME ChatGPT thread
_, r3 = manager.send_and_wait(Site.CHATGPT, f"Refine your original list using this feedback: {r2}")

# Keep the browser open as long as you like; call manager.close() when done.
```

## One-call A → B → A roundtrip

```python
from src.ai_agentic_workflow.automation.open_browser import Site, roundtrip_between_services

result = roundtrip_between_services(
    service_a=Site.CHATGPT,
    service_b=Site.PERPLEXITY,
    initial_prompt_for_a="Explain vector databases for RAG.",
    transform_a_to_b="Using the following explanation, list top 5 pitfalls practitioners face:\n\n{r1}",
)

print(result["r1"])       # (url, text)
print(result["r2"])       # (url, text)
print(result["final_a"])  # (url, text)
```

## Stock earnings analysis workflow

```python
from src.ai_agentic_workflow.automation.open_browser import stock_earnings_analysis_workflow

out = stock_earnings_analysis_workflow(lookahead_weeks=3, max_candidates=10)

print(out["parsed_tickers"])        # Extracted tickers from ChatGPT list
print(out["bullish_candidates"])    # {ticker: Perplexity bullish summary}
print(out["top_two"])               # Top two tickers chosen by ChatGPT
print(out["price_targets"])         # Per-ticker targets from ChatGPT and Perplexity
```

## Legacy helpers (single-shot)

You can still use the helpers for one-off interactions. Set `keep_browser_open=True` to keep the session alive:

```python
from src.ai_agentic_workflow.automation.open_browser import run_automation, automate_sites_in_tabs, Site

url, text = run_automation(Site.PERPLEXITY, "What is Selenium?", keep_browser_open=True)

sites_prompts = [(Site.CHATGPT, "Hello"), (Site.PERPLEXITY, "Hi")]
results = automate_sites_in_tabs(sites_prompts, keep_browser_open=True)
```

## Tips & Resilience

- The module stores and reuses conversation URLs per service, so follow-ups return to the same thread.
- Locators are resilient to minor UI changes by trying multiple selectors.
- If a CAPTCHA or re-login is shown, solve it once in the kept-open browser; subsequent steps reuse the authenticated session.
- If Chrome is not found, set `CHROME` or `CHROME_BINARY` env var to the correct binary.

## Troubleshooting

- Close any running Chrome using the `Default` profile before starting.
- Ensure `chromedriver` from `webdriver-manager` matches your installed Chrome/Chromium.
- If elements aren’t found, increase `element_wait_timeout`.
- Network errors: rerun; the session persists.
