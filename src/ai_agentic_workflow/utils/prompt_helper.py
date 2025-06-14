import logging
from pathlib import Path

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _init_() -> Path:
    """Return the prompts directory for this package."""
    try:
        # Assumes this script is somewhere within your project structure
        package_root = Path(__file__).resolve().parents[1]
    except NameError:
        # Fallback if __file__ is not defined (e.g., interactive session)
        package_root = Path(".").resolve()
        print(f"Warning: __file__ not defined. Using fallback PACKAGE_ROOT: {package_root}")

    prompts_dir = package_root / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    return prompts_dir


def get_prompt_content(prompt_name: str = None, file_name: str = None) -> str | None:
    try:
        prompt_dir = _init_()
        # Construct the full file name (e.g., "breakdown_prompt.txt")
        if file_name is None:
            file_name = f"{prompt_name}_prompt.txt"
        # Create the full path to the file
        prompt_path = prompt_dir / file_name

        logger.info(f"Attempting to load prompt from: {prompt_path}")

        # Check if the file exists before trying to open it
        if not prompt_path.is_file():
            logger.warning(f"Prompt file not found at: {prompt_path}")
            return None

        # Read the file content
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        logger.info(f"Successfully loaded prompt content: '{content}'.")
        return content

    except FileNotFoundError:
        # This case is technically covered by the is_file() check,
        # but kept for robustness.
        logger.warning(f"Prompt file not found (FileNotFoundError): {prompt_path}")
        return None
    except IOError as e:
        logger.error(f"Error reading prompt file {prompt_path}: {e}")
        return None
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"An unexpected error occurred while loading prompt '{prompt_name}': {e}")
        return None


# --- Example Usage ---
if __name__ == "__main__":

    print("\n--- Testing the prompt helper function ---")

    # 1. Load an existing prompt
    breakdown_content = get_prompt_content(file_name="breakdown_prompt.txt")
    if breakdown_content:
        print("\n[Breakdown Prompt Content]")
        print(breakdown_content)
    else:
        print("\n[Breakdown Prompt] - Could not be loaded.")

    # 2. Load another existing prompt
    summary_content = get_prompt_content(file_name="summary_prompt.txt")
    if summary_content:
        print("\n[Summary Prompt Content]")
        print(summary_content)
    else:
        print("\n[Summary Prompt] - Could not be loaded.")

    print("\n--- End of tests ---")
