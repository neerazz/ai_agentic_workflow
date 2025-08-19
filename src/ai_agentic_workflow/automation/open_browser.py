import logging
import os
import platform
import time
import traceback
from enum import Enum
from pathlib import Path

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

SITE_CONFIG = {
    Site.CHATGPT: {
        "url": "https://chat.openai.com/",
        "input_locator": (By.ID, "prompt-textarea"),
        "response_locator": (By.CSS_SELECTOR, "div.markdown"),
    },
    Site.PERPLEXITY: {
        "url": "https://www.perplexity.ai/",
        "input_locator": (
            By.CSS_SELECTOR,
            "textarea[placeholder='Ask anything…']",
        ),
        "response_locator": (By.CSS_SELECTOR, "div.prose.text-pretty"),
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


def get_chrome_executable_path() -> str:
    system = platform.system()
    candidates = []
    if system == "Darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            str(Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ]
    elif system == "Windows":
        for env in ["PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA"]:
            base = os.environ.get(env)
            if base:
                candidates.append(str(Path(base) / "Google/Chrome/Application/chrome.exe"))
    else:
        candidates = ["/usr/bin/google-chrome", "/opt/google/chrome/chrome", "/usr/bin/google-chrome-stable"]

    print(f"[DEBUG] Checking Chrome executable candidates: {candidates}")
    for p in candidates:
        if Path(p).exists():
            print(f"[DEBUG] Found Chrome executable: {p}")
            return p
    raise FileNotFoundError(f"Chrome executable not found. Checked: {candidates}")

# --- Chrome Configuration & Driver Creation ---
def configure_chrome_options(user_data_dir: str, profile_dir: str, chrome_path: str) -> Options:
    print(f"[INFO] Configuring Chrome options with user_data_dir={user_data_dir}, profile={profile_dir}")
    opts = Options()
    opts.add_argument(f"--user-data-dir={Path(user_data_dir).parent}")
    opts.add_argument(f"--profile-directory={profile_dir}")
    opts.binary_location = chrome_path
    opts.add_argument("--start-maximized")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
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


def send_prompt(driver: webdriver.Chrome, locator: tuple, text: str, timeout: int) -> None:
    print(f"[INFO] Waiting for input element {locator}...")
    wait = WebDriverWait(driver, timeout)
    el = wait.until(EC.element_to_be_clickable(locator))
    print(f"[INFO] Sending prompt text (length {len(text)} chars)")
    el.clear()
    el.send_keys(text)
    el.send_keys(Keys.ENTER)
    print("[SUCCESS] Prompt sent.")


def wait_for_response_container(driver: webdriver.Chrome, locator: tuple, timeout: int) -> None:
    print(f"[INFO] Waiting for response container {locator}...")
    WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))
    print("[SUCCESS] Response container detected.")


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


def extract_response(driver: webdriver.Chrome, locator: tuple, timeout: int) -> tuple[str, str | None]:
    print(f"[INFO] Extracting response from locator {locator}...")
    wait = WebDriverWait(driver, timeout)
    wait.until(lambda d: d.find_elements(*locator) and d.find_elements(*locator)[-1].text.strip())
    elements = driver.find_elements(*locator)
    text = elements[-1].text if elements else None
    print(f"[SUCCESS] Extracted response text (length: {len(text) if text else 0}).")
    return driver.current_url, text

# --- Main Orchestration (single-site) ---
def automate_website_interact_and_wait(
    url: str,
    input_locator: tuple,
    prompt_text: str,
    response_locator: tuple,
    element_wait_timeout: int = 30,
    user_wait_minutes: float = 2.0
) -> tuple[str, str | None]:
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
        send_prompt(driver, input_locator, prompt_text, element_wait_timeout)
        wait_for_response_container(driver, response_locator, element_wait_timeout)

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
                final_url, response_text = extract_response(driver, response_locator, element_wait_timeout)
            except Exception as e:
                print(f"[ERROR] Extraction error: {e}")
                traceback.print_exc()
            print("[INFO] Closing browser...")
            driver.quit()
            print("[SUCCESS] Browser closed.")
        print("===== Automation Finished =====\n")
    return final_url, response_text

# --- New: Multi-Tab Orchestration ---
def automate_sites_in_tabs(
    sites_prompts: list[tuple[Site, str]],
    element_wait_timeout: int = 30,
    user_wait_minutes: float = 2.0
) -> dict[Site, tuple[str, str | None]]:
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
        send_prompt(driver, cfg["input_locator"], prompt, element_wait_timeout)
        wait_for_response_container(driver, cfg["response_locator"], element_wait_timeout)

    # Post-response wait
    prompt_user_wait(user_wait_minutes)

    # Extract from each tab
    results = {}
    for site, handle, _ in tab_info:
        driver.switch_to.window(handle)
        cfg = SITE_CONFIG[site]
        final_url, text = extract_response(driver, cfg["response_locator"], element_wait_timeout)
        results[site] = (final_url, text)

    print("[INFO] Closing browser with all tabs...")
    driver.quit()
    print("===== Multi-Tab Automation Finished =====\n")
    return results

# --- High-Level Runner (single-site) ---
def run_automation(
    site: Site,
    prompt: str,
    element_wait_timeout: int = 30,
    user_wait_minutes: float = 2.0,
) -> tuple[str, str | None]:
    config = SITE_CONFIG.get(site)
    if not config:
        raise ValueError(f"Unsupported site: {site}")
    print(f"\n>>> Running automation for {site.name} <<<")
    return automate_website_interact_and_wait(
        url=config["url"],
        input_locator=config["input_locator"],
        prompt_text=prompt,
        response_locator=config["response_locator"],
        element_wait_timeout=element_wait_timeout,
        user_wait_minutes=user_wait_minutes,
    )

# --- Example Usage ---
if __name__ == "__main__":
    print(
        "\n*** IMPORTANT: Ensure ALL Chrome instances using the default profile are CLOSED before running! ***\n"
    )
    time.sleep(4)

    # Single-site example:
    # resp_url, resp_text = run_automation(Site.PERPLEXITY, "What is Selenium?")

    prompt = "What is the GIL in Python?"
    sites_prompts = [
        (Site.CHATGPT, prompt),
        (Site.PERPLEXITY, prompt),
    ]
    results = automate_sites_in_tabs(sites_prompts, user_wait_minutes=1.0)

    for site, (url, text) in results.items():
        print("\n" + "="*30)
        print(f"Site: {site.name}\nURL: {url}\nResponse:\n{text or '[No response]'}")
    print("\n[INFO] Multi-tab run complete.")
