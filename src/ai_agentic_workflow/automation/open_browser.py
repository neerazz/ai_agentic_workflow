import os

from playwright.sync_api import sync_playwright


# When doing it for the first time run the below command:
# playwright install

def run_with_persistent_profile(prompt_text: str):
    # Point this at your real Chrome/Edge profile folder:
    user_data_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome/Profile 1")

    with sync_playwright() as p:
        # Launch a new browser process, but with your existing profile data:
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,  # show the window
            args=["--start-maximized"]
        )
        page = context.new_page()
        page.goto("https://chat.openai.com/")

        # Now just fill and send—you're already logged in:
        page.fill('textarea[placeholder*="Send a message"]', prompt_text)
        page.keyboard.press("Enter")
        page.wait_for_selector(".chat-response")  # adjust to actual response selector

        print("✅ Prompt sent!")
        context.close()


if __name__ == "__main__":
    run_with_persistent_profile("Hello from Playwright with profile! Can you tell me who am I..")
