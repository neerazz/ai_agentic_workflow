import logging
import os
import platform
import re
import time
import traceback
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

# --- Supported Sites ---
class Site(Enum):
    CHATGPT = "chatgpt"
    PERPLEXITY = "perplexity"

SITE_CONFIG: Dict[Site, Dict[str, object]] = {
    Site.CHATGPT: {
        # ChatGPT now commonly serves on chatgpt.com; keep compatibility with existing sessions
        "url": "https://chatgpt.com/",
        # Try multiple locators for robustness; first matching & clickable will be used
        "input_locators": [
            (By.ID, "prompt-textarea"),
            (By.CSS_SELECTOR, "textarea#prompt-textarea"),
            (By.CSS_SELECTOR, "textarea[placeholder*='message']"),
        ],
        "response_locators": [
            (By.CSS_SELECTOR, "div[data-message-author-role='assistant'] div.markdown"),
            (By.CSS_SELECTOR, "div.markdown"),
        ],
    },
    Site.PERPLEXITY: {
        "url": "https://www.perplexity.ai/",
        "input_locators": [
            (By.CSS_SELECTOR, "textarea[placeholder='Ask anything…']"),
            (By.CSS_SELECTOR, "textarea[placeholder='Ask anything...']"),
            (By.CSS_SELECTOR, "textarea"),
        ],
        "response_locators": [
            (By.CSS_SELECTOR, "div.prose.text-pretty"),
            (By.CSS_SELECTOR, "div[data-testid='answer-content']"),
        ],
    },
}

# --- Helper Functions ---
def get_default_chrome_user_data_dir() -> str:
    system = platform.system()
    if system == "Darwin":
        path = Path.home() / "Library/Application Support/Google/Chrome/Default"
    elif system == "Windows":
        local = os.environ.get("LOCALAPPDATA") or (
            Path(os.environ.get("USERPROFILE", "")) / "AppData/Local"
        )
        path = Path(local) / "Google/Chrome/User Data/Default"
    else:
        path = Path.home() / ".config/google-chrome/Default"

    print(f"[DEBUG] Default Chrome user data dir: {path}")
    if not path.exists():
        print(f"[WARNING] User data dir not found: {path}")
    return str(path)


def get_chrome_executable_path() -> Optional[str]:
    system = platform.system()
    env_overrides = [
        os.environ.get("CHROME").strip() if os.environ.get("CHROME") else None,
        os.environ.get("CHROME_BINARY").strip() if os.environ.get("CHROME_BINARY") else None,
        os.environ.get("GOOGLE_CHROME_SHIM").strip() if os.environ.get("GOOGLE_CHROME_SHIM") else None,
    ]
    env_overrides = [p for p in env_overrides if p]

    candidates: List[str] = []
    if system == "Darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            str(Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    elif system == "Windows":
        for env in ["PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA"]:
            base = os.environ.get(env)
            if base:
                candidates.append(str(Path(base) / "Google/Chrome/Application/chrome.exe"))
                candidates.append(str(Path(base) / "Chromium/Application/chrome.exe"))
    else:
        candidates = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/opt/google/chrome/chrome",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
        ]

    print(f"[DEBUG] Checking Chrome executable env overrides: {env_overrides}")
    for p in env_overrides + candidates:
        try:
            if p and Path(p).exists():
                print(f"[DEBUG] Found Chrome executable: {p}")
                return p
        except Exception:
            continue
    print("[WARNING] Chrome/Chromium executable not found via known paths; relying on system default.")
    # Returning None signals to not set binary_location; chromedriver will use system default
    return None

# --- Chrome Configuration & Driver Creation ---
def configure_chrome_options(user_data_dir: str, profile_dir: str, chrome_path: Optional[str]) -> Options:
    print(f"[INFO] Configuring Chrome options with user_data_dir={user_data_dir}, profile={profile_dir}")
    opts = Options()
    opts.add_argument(f"--user-data-dir={Path(user_data_dir).parent}")
    opts.add_argument(f"--profile-directory={profile_dir}")
    if chrome_path:
        opts.binary_location = chrome_path
    opts.add_argument("--start-maximized")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    # Avoid immediate quit when last tab closes (keep-alive managed by code, not Chrome flags)
    return opts


def create_driver(options: Options) -> webdriver.Chrome:
    print("[INFO] Creating ChromeDriver service and launching browser...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print("[SUCCESS] ChromeDriver initialized.")
    return driver

# --- Persistent Session Helpers ---
def start_persistent_browser(profile_dir: str = "Default") -> webdriver.Chrome | None:
    """
    Starts a Chrome browser using the user's default profile so sessions persist
    (avoids repeated logins/CAPTCHAs). Returns a live webdriver instance.
    """
    try:
        import os as _os
        if _os.getenv("DISABLE_BROWSER", "0") == "1":
            logger.warning("Browser disabled via DISABLE_BROWSER env var. Returning None driver.")
            return None
        user_data_dir = get_default_chrome_user_data_dir()
        chrome_path = get_chrome_executable_path()
        opts = configure_chrome_options(user_data_dir, profile_dir, chrome_path)
        return create_driver(opts)
    except Exception as e:
        logger.warning("Could not start persistent browser: %s. Falling back to API-only.", e)
        return None


def ensure_site_open(driver: webdriver.Chrome, site: Site, timeout: int = 30) -> None:
    """
    Navigates the current tab to the target site if not already there.
    """
    cfg = SITE_CONFIG[site]
    try:
        if cfg["url"] not in driver.current_url:
            navigate_to_site(driver, cfg["url"], timeout)
    except Exception:
        navigate_to_site(driver, cfg["url"], timeout)


def run_prompt_in_existing_tab(
    driver: webdriver.Chrome | None,
    site: Site,
    prompt_text: str,
    element_wait_timeout: int = 30
) -> tuple[str, str | None]:
    """
    Reuses an existing driver/tab to send a prompt to the given site and extract the response.
    Keeps the browser open for subsequent calls.
    """
    if driver is None:
        raise RuntimeError("No browser driver available")
    cfg = SITE_CONFIG[site]
    ensure_site_open(driver, site, element_wait_timeout)
    send_prompt(driver, cfg["input_locator"], prompt_text, element_wait_timeout)
    wait_for_response_container(driver, cfg["response_locator"], element_wait_timeout)
    final_url, text = extract_response(driver, cfg["response_locator"], element_wait_timeout)
    return final_url, text


def close_browser(driver: webdriver.Chrome | None) -> None:
    if driver is None:
        return
    try:
        driver.quit()
    except Exception:
        pass

# --- Interaction Steps ---
def navigate_to_site(driver: webdriver.Chrome, url: str, timeout: int) -> None:
    print(f"[INFO] Navigating to {url}...")
    driver.get(url)
    WebDriverWait(driver, timeout).until(lambda d: d.current_url.startswith("http"))
    print(f"[SUCCESS] Arrived at {driver.current_url}")


def _find_clickable_any(driver: webdriver.Chrome, locators: List[tuple], timeout: int):
    last_error: Optional[Exception] = None
    for locator in locators:
        try:
            print(f"[INFO] Trying locator {locator}...")
            el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
            return el, locator
        except Exception as e:
            last_error = e
            continue
    if last_error:
        raise last_error
    raise TimeoutException("No clickable element found for provided locators")


def send_prompt(driver: webdriver.Chrome, locators: List[tuple], text: str, timeout: int) -> None:
    print(f"[INFO] Waiting for any input element from {len(locators)} candidates...")
    el, used_locator = _find_clickable_any(driver, locators, timeout)
    print(f"[INFO] Using input locator {used_locator}; sending prompt text (length {len(text)} chars)")
    try:
        el.clear()
    except Exception:
        pass
    el.send_keys(text)
    el.send_keys(Keys.ENTER)
    print("[SUCCESS] Prompt sent.")


def wait_for_response_container(driver: webdriver.Chrome, locators: List[tuple], timeout: int) -> None:
    print(f"[INFO] Waiting for response container from {len(locators)} candidates...")
    last_error: Optional[Exception] = None
    for locator in locators:
        try:
            WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))
            print(f"[SUCCESS] Response container detected with locator {locator}.")
            return
        except Exception as e:
            last_error = e
            continue
    if last_error:
        raise last_error
    raise TimeoutException("No response container became present in time")


def prompt_user_wait(initial_minutes: float) -> float:
    minutes = initial_minutes
    print(f"[INFO] Post-response wait is set to {minutes} minute(s)")
    while minutes < 0:
        try:
            minutes = float(input("Enter wait time in minutes: "))
        except ValueError:
            print("Invalid input, try again.")
    if minutes > 0:
        print(f"[INFO] Sleeping for {minutes} minute(s)...")
        time.sleep(minutes * 60)
        print("[INFO] Post-response wait complete.")
    return minutes


def extract_response(driver: webdriver.Chrome, locators: List[tuple], timeout: int) -> tuple[str, Optional[str]]:
    print(f"[INFO] Extracting response from candidate locators...")
    last_text: Optional[str] = None
    for locator in locators:
        try:
            wait = WebDriverWait(driver, timeout)
            wait.until(lambda d: d.find_elements(*locator) and d.find_elements(*locator)[-1].text.strip())
            elements = driver.find_elements(*locator)
            if elements:
                last_text = elements[-1].text
                break
        except Exception:
            continue
    print(f"[SUCCESS] Extracted response text (length: {len(last_text) if last_text else 0}).")
    return driver.current_url, last_text

# --- Main Orchestration (single-site) ---
def automate_website_interact_and_wait(
    url: str,
    input_locators: List[tuple],
    prompt_text: str,
    response_locators: List[tuple],
    element_wait_timeout: int = 30,
    user_wait_minutes: float = 2.0,
    keep_browser_open: bool = False,
) -> tuple[str, Optional[str]]:
    print("\n===== Automation Started =====")
    driver = None
    final_url = url
    response_text = None
    try:
        user_data_dir = get_default_chrome_user_data_dir()
        chrome_path = get_chrome_executable_path()
        opts = configure_chrome_options(user_data_dir, "Default", chrome_path)
        driver = create_driver(opts)

        navigate_to_site(driver, url, element_wait_timeout)
        send_prompt(driver, input_locators, prompt_text, element_wait_timeout)
        wait_for_response_container(driver, response_locators, element_wait_timeout)

    except (FileNotFoundError, TimeoutException, NoSuchElementException) as e:
        print(f"[ERROR] Automation error: {e}")
        traceback.print_exc()
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        traceback.print_exc()
    finally:
        if driver:
            prompt_user_wait(user_wait_minutes)
            try:
                final_url, response_text = extract_response(driver, response_locators, element_wait_timeout)
            except Exception as e:
                print(f"[ERROR] Extraction error: {e}")
                traceback.print_exc()
            if keep_browser_open:
                print("[INFO] Keeping browser open for session reuse.")
            else:
                print("[INFO] Closing browser...")
                driver.quit()
                print("[SUCCESS] Browser closed.")
        print("===== Automation Finished =====\n")
    return final_url, response_text

# --- New: Multi-Tab Orchestration ---
def automate_sites_in_tabs(
    sites_prompts: List[tuple[Site, str]],
    element_wait_timeout: int = 30,
    user_wait_minutes: float = 2.0,
    keep_browser_open: bool = False,
) -> Dict[Site, tuple[str, Optional[str]]]:
    print("\n===== Multi-Tab Automation Started =====")
    # Setup driver once
    user_data_dir = get_default_chrome_user_data_dir()
    chrome_path = get_chrome_executable_path()
    opts = configure_chrome_options(user_data_dir, "Default", chrome_path)
    driver = create_driver(opts)

    # Track tabs: [(site, handle, prompt)]
    tab_info = []
    for idx, (site, prompt) in enumerate(sites_prompts):
        if idx == 0:
            handle = driver.current_window_handle
        else:
            print(f"[INFO] Opening new tab for {site.name}")
            driver.execute_script("window.open('');")
            handle = driver.window_handles[-1]
        tab_info.append((site, handle, prompt))
        driver.switch_to.window(handle)
        cfg = SITE_CONFIG[site]
        navigate_to_site(driver, cfg["url"], element_wait_timeout)
        send_prompt(driver, cfg["input_locators"], prompt, element_wait_timeout)
        wait_for_response_container(driver, cfg["response_locators"], element_wait_timeout)

    # Post-response wait
    prompt_user_wait(user_wait_minutes)

    # Extract from each tab
    results: Dict[Site, tuple[str, Optional[str]]] = {}
    for site, handle, _ in tab_info:
        driver.switch_to.window(handle)
        cfg = SITE_CONFIG[site]
        final_url, text = extract_response(driver, cfg["response_locators"], element_wait_timeout)
        results[site] = (final_url, text)

    if keep_browser_open:
        print("[INFO] Keeping browser open with all tabs for session reuse.")
    else:
        print("[INFO] Closing browser with all tabs...")
        driver.quit()
    print("===== Multi-Tab Automation Finished =====\n")
    return results

# --- Persistent Session Manager ---
class BrowserSessionManager:
    def __init__(
        self,
        user_data_dir: Optional[str] = None,
        profile_dir: str = "Default",
        chrome_path: Optional[str] = None,
        element_wait_timeout: int = 30,
    ) -> None:
        self.user_data_dir = user_data_dir or get_default_chrome_user_data_dir()
        self.profile_dir = profile_dir
        self.chrome_path = chrome_path or get_chrome_executable_path()
        self.element_wait_timeout = element_wait_timeout
        self.driver: Optional[webdriver.Chrome] = None
        self.site_to_tab: Dict[Site, str] = {}
        self.site_to_conversation_url: Dict[Site, str] = {}

    def ensure_driver(self) -> webdriver.Chrome:
        if self.driver is None:
            print("[INFO] Initializing persistent browser session...")
            opts = configure_chrome_options(self.user_data_dir, self.profile_dir, self.chrome_path)
            self.driver = create_driver(opts)
        return self.driver

    def open_or_switch_tab(self, site: Site) -> None:
        driver = self.ensure_driver()
        if site in self.site_to_tab and self.site_to_tab[site] in driver.window_handles:
            driver.switch_to.window(self.site_to_tab[site])
            return
        driver.execute_script("window.open('');")
        handle = driver.window_handles[-1]
        self.site_to_tab[site] = handle
        driver.switch_to.window(handle)

    def navigate_to_conversation(self, site: Site) -> None:
        driver = self.ensure_driver()
        self.open_or_switch_tab(site)
        cfg = SITE_CONFIG[site]
        url = self.site_to_conversation_url.get(site, cfg["url"])  # type: ignore[index]
        navigate_to_site(driver, url, self.element_wait_timeout)

    def send_and_wait(self, site: Site, prompt_text: str) -> Tuple[str, Optional[str]]:
        driver = self.ensure_driver()
        self.open_or_switch_tab(site)
        cfg = SITE_CONFIG[site]
        # Always ensure we are at the conversation URL if known
        if site in self.site_to_conversation_url:
            navigate_to_site(driver, self.site_to_conversation_url[site], self.element_wait_timeout)
        else:
            navigate_to_site(driver, cfg["url"], self.element_wait_timeout)  # type: ignore[index]
        send_prompt(driver, cfg["input_locators"], prompt_text, self.element_wait_timeout)  # type: ignore[index]
        wait_for_response_container(driver, cfg["response_locators"], self.element_wait_timeout)  # type: ignore[index]
        final_url, text = extract_response(driver, cfg["response_locators"], self.element_wait_timeout)  # type: ignore[index]
        # Store conversation URL for future follow-ups (most sites keep thread in URL)
        self.site_to_conversation_url[site] = final_url
        return final_url, text

    def close(self) -> None:
        if self.driver is not None:
            print("[INFO] Closing persistent browser session...")
            try:
                self.driver.quit()
            finally:
                self.driver = None
                self.site_to_tab.clear()
                self.site_to_conversation_url.clear()


# --- Cross-service roundtrip: A -> B -> A (reuse same conversations)
def roundtrip_between_services(
    service_a: Site,
    service_b: Site,
    initial_prompt_for_a: str,
    transform_a_to_b: Optional[str] = None,
    element_wait_timeout: int = 30,
) -> Dict[str, Tuple[str, Optional[str]]]:
    """
    Orchestrates: send to A, take response r1 -> send to B, get r2 -> send r2 back to A in the SAME conversation.

    transform_a_to_b: Optional template to wrap r1 for service B, e.g.
        "Using the following context, perform X and return Y:\n\n{r1}"
    Returns a dict with keys: "r1", "r2", and "final_a" mapping to (url, text)
    """
    manager = BrowserSessionManager(element_wait_timeout=element_wait_timeout)
    # Step 1: A
    a_url_1, r1 = manager.send_and_wait(service_a, initial_prompt_for_a)
    # Step 2: B
    b_prompt = (transform_a_to_b or "{r1}").format(r1=r1 or "")
    b_url, r2 = manager.send_and_wait(service_b, b_prompt)
    # Step 3: Back to A in same conversation
    final_a_url, final_a_text = manager.send_and_wait(service_a, r2 or "Please proceed with this result.")
    return {
        "r1": (a_url_1, r1),
        "r2": (b_url, r2),
        "final_a": (final_a_url, final_a_text),
    }


# --- Stock Earnings Analysis Workflow ---
def _parse_tickers_from_text(text: str) -> List[str]:
    # Simple heuristic: tickers are uppercase 1-5 letters, optionally with dot (e.g., BRK.B)
    candidates = re.findall(r"\b[A-Z]{1,5}(?:\.[A-Z])?\b", text or "")
    # Filter common English words accidentally captured
    blacklist = {"AND", "FOR", "THE", "WITH", "WEEK", "NEXT", "DUE", "WEEKS"}
    return [t for t in candidates if t not in blacklist]


def stock_earnings_analysis_workflow(
    lookahead_weeks: int = 3,
    max_candidates: int = 10,
    element_wait_timeout: int = 45,
) -> Dict[str, object]:
    """
    Workflow:
    1) Ask ChatGPT for stocks with earnings in next N weeks; ask it to filter to mid/large cap growth potential, return ~10 tickers.
    2) For each ticker, ask Perplexity for a concise fundamental/technical read and a single-line verdict 'Bullish' or 'Bearish'.
    3) Keep only 'Bullish'; send the bullish subset back to ChatGPT asking to pick top 2 with rationale.
    4) For top 2, ask both ChatGPT and Perplexity for 3-month price target, percentage growth, and probability distribution of outcomes.
    All steps reuse the same open browser sessions and prior conversations/tabs.
    """
    manager = BrowserSessionManager(element_wait_timeout=element_wait_timeout)

    # Step 1: ChatGPT list + filtering
    prompt_a = (
        f"List U.S.-listed stocks with earnings in the next {lookahead_weeks} weeks. "
        f"Filter to ~{max_candidates} mid/large-cap names with strong growth potential. "
        "Return just a bullet list of tickers and company names."
    )
    chatgpt_url_1, list_text = manager.send_and_wait(Site.CHATGPT, prompt_a)
    tickers = _parse_tickers_from_text(list_text or "")[: max_candidates * 2]

    # Step 2: Perplexity analysis per ticker
    bullish_summaries: Dict[str, str] = {}
    analysis_prompt_template = (
        "You are a financial analyst. For ticker {ticker}, provide a concise synthesis of recent news, "
        "fundamentals, and price action relevant to upcoming earnings. "
        "Conclude with a single line strictly formatted as Verdict: Bullish or Verdict: Bearish."
    )
    for ticker in tickers:
        prompt_b = analysis_prompt_template.format(ticker=ticker)
        _, analysis_text = manager.send_and_wait(Site.PERPLEXITY, prompt_b)
        if analysis_text and re.search(r"Verdict:\s*Bullish", analysis_text, re.IGNORECASE):
            bullish_summaries[ticker] = analysis_text
        # Limit to reasonable number to avoid rate limits
        if len(bullish_summaries) >= max_candidates:
            break

    # Step 3: Ask ChatGPT to pick top 2 from bullish set
    if not bullish_summaries:
        selection_text = "No bullish candidates identified by Perplexity."
        top_two = []
    else:
        combined_context = "\n\n".join([
            f"Ticker: {t}\nSummary from Perplexity:\n{txt}" for t, txt in bullish_summaries.items()
        ])
        pick_prompt = (
            "From the following bullish candidates (summaries from Perplexity), pick the top 2 tickers "
            "with the strongest bullish potential ahead of earnings. Provide a short rationale and list only the two tickers at the top.\n\n"
            f"{combined_context}"
        )
        _, selection_text = manager.send_and_wait(Site.CHATGPT, pick_prompt)
        # Naive extraction of top 2 tickers from ChatGPT response
        top_two = _parse_tickers_from_text(selection_text or "")[:2]

    # Step 4: Price targets for top 2 from both services
    price_target_results: Dict[str, Dict[str, Tuple[str, Optional[str]]]] = {}
    if top_two:
        target_prompt_template = (
            "Give a 3-month price target for {ticker}, expected % growth from current price, "
            "and a brief probability distribution for downside/base/upside scenarios. Keep it concise."
        )
        for ticker in top_two:
            pt_prompt = target_prompt_template.format(ticker=ticker)
            cg_url, cg_text = manager.send_and_wait(Site.CHATGPT, pt_prompt)
            px_url, px_text = manager.send_and_wait(Site.PERPLEXITY, pt_prompt)
            price_target_results[ticker] = {
                "chatgpt": (cg_url, cg_text),
                "perplexity": (px_url, px_text),
            }

    return {
        "chatgpt_list_url": chatgpt_url_1,
        "initial_list_text": list_text,
        "parsed_tickers": tickers,
        "bullish_candidates": bullish_summaries,
        "chatgpt_selection_text": selection_text,
        "top_two": top_two,
        "price_targets": price_target_results,
    }

# --- High-Level Runner (single-site) ---
def run_automation(
    site: Site,
    prompt: str,
    element_wait_timeout: int = 30,
    user_wait_minutes: float = 2.0,
    keep_browser_open: bool = False,
) -> tuple[str, Optional[str]]:
    config = SITE_CONFIG.get(site)
    if not config:
        raise ValueError(f"Unsupported site: {site}")
    print(f"\n>>> Running automation for {site.name} <<<")
    return automate_website_interact_and_wait(
        url=config["url"],  # type: ignore[index]
        input_locators=config["input_locators"],  # type: ignore[index]
        prompt_text=prompt,
        response_locators=config["response_locators"],  # type: ignore[index]
        element_wait_timeout=element_wait_timeout,
        user_wait_minutes=user_wait_minutes,
        keep_browser_open=keep_browser_open,
    )

# --- Example Usage ---
if __name__ == "__main__":
    print(
        "\n*** IMPORTANT: Ensure ALL Chrome instances using the default profile are CLOSED before running! ***\n"
    )
    time.sleep(4)

    # Single-site example:
    # resp_url, resp_text = run_automation(Site.PERPLEXITY, "What is Selenium?", keep_browser_open=True)

    prompt = "What is the GIL in Python?"
    sites_prompts = [
        (Site.CHATGPT, prompt),
        (Site.PERPLEXITY, prompt),
    ]
    results = automate_sites_in_tabs(sites_prompts, user_wait_minutes=1.0, keep_browser_open=True)

    for site, (url, text) in results.items():
        print("\n" + "="*30)
        print(f"Site: {site.name}\nURL: {url}\nResponse:\n{text or '[No response]'}")
    print("\n[INFO] Multi-tab run complete.")
