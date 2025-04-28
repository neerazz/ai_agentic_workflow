# deepseek_lmstudio_client.py

import logging

from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)


class DeepseekLMStudioClient:
    """
    Adapter for LM Studio’s OpenAI-compatible HTTP API (openai-python v1.x).
    """

    def __init__(
            self,
            model_name: str = "deepseek-r1-distill-llama-8b",
            base_url: str = "http://localhost:1234/v1",  # LM Studio's OpenAI base
    ):
        # Instantiate the v1.x client pointing at your local LM Studio server
        self.client = OpenAI(
            api_key="",  # LM Studio typically doesn’t require an API key
            api_base=base_url,  # e.g. "http://localhost:1234/v1"
        )
        self.model_name = model_name

    def __call__(self, prompt: str) -> str:
        logger.info("Sending prompt to LM Studio model %s: %s", self.model_name, prompt)
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            # Grab the text from the first choice
            return response.choices[0].message.content.strip()

        except OpenAIError as e:
            logger.error("LM Studio API error: %s", e, exc_info=True)
            return f"Error from LM Studio API: {e}"


# --- Example usage ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    client = DeepseekLMStudioClient(
        model_name="deepseek-r1-distill-llama-8b",
        base_url="http://127.0.0.1:1234/v1"
    )

    print("--- Factorial Function ---")
    print(client("Write a Python function to calculate the factorial of a number."))

    print("\n--- Recursion Explanation ---")
    print(client("Explain the concept of recursion in simple terms."))
