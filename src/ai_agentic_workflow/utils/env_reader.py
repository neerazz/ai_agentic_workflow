import os
from dotenv import load_dotenv

# Load environment variables from .env at project root
load_dotenv()

def get_env_variable(name: str) -> str:
    """
    Fetches the environment variable or raises an error if not found.
    """
    value = os.getenv(name)
    if value is None:
        raise KeyError(f"Environment variable '{name}' is not set.")
    return value