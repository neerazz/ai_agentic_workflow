import logging
import os
import platform
import time
import traceback
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

# --- Helper Functions ---

logger = logging.getLogger(__name__)

def get_default_chrome_user_data_dir() -> str:
    """Returns the path to the default Chrome user data directory."""
    system = platform.system()
    if system == "Darwin":
        path = (
            Path.home()
            / "Library"
            / "Application Support"
            / "Google"
            / "Chrome"
            / "Default"
        )
    elif system == "Windows":
        local = os.environ.get("LOCALAPPDATA", "")
        if not local:
            user_profile = os.environ.get("USERPROFILE", "")
            if not user_profile:
                raise OSError("Could not determine user profile directory.")
            local = str(Path(user_profile) / "AppData" / "Local")
        path = Path(local) / "Google" / "Chrome" / "User Data" / "Default"
    else:
        path = Path.home() / ".config" / "google-chrome" / "Default"

    print(f"[DEBUG] Determined default user data dir: {path}")
    if not path.exists():
        print(f"[WARNING] Default user data directory not found at: {path}")
    return str(path)


def get_chrome_executable_path() -> str:
    """Returns the path to the Chrome executable, checking common locations."""
    system = platform.system()
    paths_to_check = []

    if system == "Darwin":
        paths_to_check.extend([
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            str(Path.home() / "Applications" / "Google Chrome.app" / "Contents" / "MacOS" / "Google Chrome")
        ])
    elif system == "Windows":
        prog_files_x86 = os.environ.get("PROGRAMFILES(X86)", "")
        if prog_files_x86:
            paths_to_check.append(str(Path(prog_files_x86) / "Google" / "Chrome" / "Application" / "chrome.exe"))
        prog_files = os.environ.get("PROGRAMFILES", "")
        if prog_files:
            paths_to_check.append(str(Path(prog_files) / "Google" / "Chrome" / "Application" / "chrome.exe"))
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            paths_to_check.append(str(Path(local_app_data) / "Google" / "Chrome" / "Application" / "chrome.exe"))
    else:  # Linux
        paths_to_check.extend([
            "/usr/bin/google-chrome",
            "/opt/google/chrome/chrome",
            "/usr/bin/google-chrome-stable",
        ])

    print("[DEBUG] Checking potential Chrome executable paths:")
    for path_str in paths_to_check:
        print(f"[DEBUG]  - {path_str}")
        if Path(path_str).exists():
            print(f"[DEBUG] Found Chrome executable at: {path_str}")
            return path_str

    raise FileNotFoundError(f"Cannot find Chrome executable. Checked: {paths_to_check}")


# --- Main Selenium Automation Function ---

def automate_website_interact_and_wait(
    url: str,
    input_locator: tuple,
    prompt_text: str,
    response_locator: tuple,
    element_wait_timeout_seconds: int = 30, # Timeout for finding elements (seconds)
    user_wait_minutes: float = 2.0 # Delay after detecting response text
) -> tuple[str, str | None]:
    """
    Automates interaction, extracts text, waits, and returns URL+response.

    Launches Chrome with default profile, navigates, interacts, waits for response,
    extracts text, prompts user for wait time, waits, closes browser.

    Args:
        url: The target website URL.
        input_locator: Tuple (By strategy, value) for the input field.
        prompt_text: Text to enter.
        response_locator: Tuple (By strategy, value) for the response container.
        element_wait_timeout_seconds: Max seconds to wait for elements.
        post_response_delay_seconds: Seconds to wait after detecting response text.

    Returns:
        A tuple containing (url, extracted_response_text).
        extracted_response_text is None if an error occurred.
    """
    driver = None
    response_text = None
    final_url = url # <<-- Initialize final_url
    start_time = time.time()
    print(f"\n{'='*15} Automation Started {'='*15}")

    try:
        print("[INFO] Finding Chrome profile and executable paths...")
        user_data_dir = get_default_chrome_user_data_dir()
        chrome_executable_path = get_chrome_executable_path()
        profile_dir = "Default"
        user_data_path = str(Path(user_data_dir).parent) # Need parent dir for --user-data-dir

        print(f"[INFO] Target URL: {url}")
        print(f"[INFO] Using Profile: {user_data_path} / {profile_dir}")
        print("[INFO] Configuring Chrome options...")
        chrome_options = Options()
        chrome_options.add_argument(f"--user-data-dir={user_data_path}")
        chrome_options.add_argument(f"--profile-directory={profile_dir}")
        chrome_options.binary_location = chrome_executable_path
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        print("[INFO] Setting up ChromeDriver service...")
        service = Service(ChromeDriverManager().install())

        print("[INFO] Launching Chrome browser...")
        # Ensure previous Chrome instance using this profile is closed!
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("[SUCCESS] Chrome launched successfully.")

        wait = WebDriverWait(driver, element_wait_timeout_seconds)

        print(f"[INFO] Navigating to {url}...")
        driver.get(url)
        print(f"[SUCCESS] Navigation to {url} complete.")

        print(f"[INFO] Waiting for input element: {input_locator}...")
        input_element = wait.until(EC.element_to_be_clickable(input_locator))
        print("[SUCCESS] Input element found and clickable.")

        print(f"[INFO] Entering prompt (first 50 chars): '{prompt_text[:50]}...'")
        input_element.clear()
        input_element.send_keys(prompt_text)
        input_element.send_keys(Keys.ENTER)
        print("[SUCCESS] Prompt entered and Enter key pressed.")

        print(f"[INFO] Waiting for response container element: {response_locator}...")
        wait.until(EC.presence_of_element_located(response_locator))
        print("[SUCCESS] Response container located.")

        print(f"[INFO] Waiting for text to appear in the last response element...")

    except FileNotFoundError as e:
        print(f"[ERROR] File Not Found: {e}")
        print("[ERROR] Could not find Chrome executable or user data directory.")
    except TimeoutException:
        print(f"[ERROR] Timed out waiting for element.")
        print(f"  Input Locator: {input_locator}")
        print(f"  Response Locator: {response_locator}")
        print(f"  Timeout Setting: {element_wait_timeout_seconds}s")
        traceback.print_exc()
    except NoSuchElementException as e:
        print(f"[ERROR] Could not find element: {e}")
        print(f"  Locator possibly involved: {e.msg}") # Selenium often includes locator in msg
        traceback.print_exc()
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")
        traceback.print_exc()

    finally:
        # This block executes whether the try block succeeded or failed
        print("\n--- Entering Finally Block (Wait/Cleanup) ---")
        if driver: # Only proceed if driver was initialized
            print("[INFO] Prompting for wait time before closing browser...")
            while user_wait_minutes < 0:
                try:
                    wait_input = input(">>> Enter wait time in MINUTES before closing (e.g., 5, 0.5, or 0 to close now): ")
                    user_wait_minutes = float(wait_input)
                    if user_wait_minutes < 0:
                        print("   [WARN] Please enter a non-negative number.")
                except ValueError:
                    print("   [WARN] Invalid input. Please enter a number.")
                except EOFError:
                    print("   [WARN] Input stream closed. Defaulting to 0 minutes wait.")
                    user_wait_minutes = 0.0 # Default to 0 if input fails

            print(f"[INFO] Applying post-response delay: {user_wait_minutes}s...")
            if user_wait_minutes > 0:
                wait_seconds = user_wait_minutes * 60
                print(f"[INFO] Waiting for {user_wait_minutes:.2f} minute(s) ({int(wait_seconds)} seconds)...")
                try:
                    time.sleep(wait_seconds)
                    print("[INFO] Wait finished.")
                except KeyboardInterrupt:
                    print("\n[WARN] Wait interrupted by user (Ctrl+C).")
            else:
                print("[INFO] Skipping wait (time <= 0).")

            print("[INFO] Attempting final text extraction from the last matching element...")
            # Wait until the *last* element matching the locator has some text
            wait.until(lambda d: d.find_elements(*response_locator) and d.find_elements(*response_locator)[-1].text.strip() != "")
            print("[SUCCESS] Initial text detected in response element.")
            try:
                final_url = driver.current_url # Capture the final URL after interaction
                all_response_elements = driver.find_elements(*response_locator)
                if all_response_elements:
                    response_element = all_response_elements[-1]
                    response_text = response_element.text
                    print(f"[SUCCESS] Response text extracted (length: {len(response_text)}).")
                else:
                    print("[WARNING] Response element locator matched earlier, but no elements found now.")
                    response_text = None
            except Exception as find_err:
                print(f"[ERROR] Failed during final text/URL extraction: {find_err}")
                # Attempt to get URL even if text extraction fails
                if driver and final_url is None:
                    try:
                        final_url = driver.current_url
                        print(f"[DEBUG] Captured final URL after text extraction error: {final_url}")
                    except Exception as url_err:
                        print(f"[ERROR] Failed to capture final URL after text error: {url_err}")
                traceback.print_exc()
                response_text = None # Ensure text is None on error

            print("[INFO] Closing the browser...")
            driver.quit()
            print("[SUCCESS] Browser closed.")
        else:
             print("[WARN] Driver was not initialized, cannot perform wait or close actions.")

        end_time = time.time()
        print(f"\n{'='*15} Automation Finished (Total time: {end_time - start_time:.2f}s) {'='*15}")

    # Return the URL and the extracted text (or None)
    return (final_url, response_text)


# --- Example Usage ---
if __name__ == "__main__":

    # --- Configuration ---
    target_url = "https://chat.openai.com/"
    # Use DevTools (F12) to verify these locators on the target site
    chat_input_locator = (By.ID, "prompt-textarea")
    chat_response_locator = (By.CSS_SELECTOR, "div.markdown") # Targets the main response text container

    prompt = "Explain Python's Global Interpreter Lock (GIL) in simple terms."

    # --- Pre-run Check ---
    print("\n*** IMPORTANT: Ensure ALL Chrome instances using the default profile are CLOSED before running! ***\n")
    time.sleep(4) # Give user time to read

    # --- Run the Automation ---
    returned_url, extracted_response = automate_website_interact_and_wait(
        url=target_url,
        input_locator=chat_input_locator,
        prompt_text=prompt,
        response_locator=chat_response_locator,
        element_wait_timeout_seconds=30, # How long to wait for elements to appear
        user_wait_minutes=1.0   # How long to wait after response text starts appearing
    )

    # --- Print the Final Result ---
    print("\n" + "=" * 40)
    print("            FINAL RESULT")
    print("-" * 40)
    print(f"URL Visited: {returned_url}")
    print("-" * 40)
    if extracted_response:
        print("Extracted Response:")
        print(extracted_response)
    else:
        print("Response Text: [Could not be extracted or an error occurred]")
    print("=" * 40 + "\n")

    print("[INFO] Script execution complete.")