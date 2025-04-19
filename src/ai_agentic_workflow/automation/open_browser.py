import os
import platform
from pathlib import Path
from playwright.sync_api import sync_playwright


# When doing it for the first time run the below command:
# playwright install

def get_default_chrome_user_data_dir() -> str:
    """
    Returns the path to the default Chrome user data directory for the current OS.
    """
    system = platform.system()
    if system == "Darwin":
        return str(Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "Default")
    elif system == "Windows":
        local = os.environ.get("LOCALAPPDATA", "")
        return str(Path(local) / "Google" / "Chrome" / "User Data" / "Default")
    else:
        return str(Path.home() / ".config" / "google-chrome" / "Default")


def get_chrome_executable_path() -> str:
    """
    Returns the path to the Chrome executable for the current OS.
    """
    system = platform.system()
    if system == "Darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif system == "Windows":
        program_files = os.environ.get("PROGRAMFILES", "")
        return str(Path(program_files) / "Google" / "Chrome" / "Application" / "chrome.exe")
    else:
        return "/usr/bin/google-chrome"


def run_with_persistent_profile(prompt_text: str):
    # Point this at your real Chrome/Edge profile folder:
    user_data_dir = get_default_chrome_user_data_dir()
    chrome_executable_path = get_chrome_executable_path()  # Get the Chrome executable path

    with sync_playwright() as p:
        # Launch a new browser process, but with your existing profile data:
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            executable_path=chrome_executable_path,  # Use the regular Chrome browser
            headless=False,  # Show the window
            args=["--start-maximized"]
        )
        page = context.new_page()
        page.goto("https://chat.openai.com/")

        # Now just fill and send—you're already logged in:
        page.fill('textarea[placeholder*="Send a message"]', prompt_text)
        page.keyboard.press("Enter")
        page.wait_for_selector(".chat-response")  # Adjust to actual response selector

        print("✅ Prompt sent!")
        context.close()


if __name__ == "__main__":
    run_with_persistent_profile("Hello from Playwright with profile! Can you tell me who am I..")