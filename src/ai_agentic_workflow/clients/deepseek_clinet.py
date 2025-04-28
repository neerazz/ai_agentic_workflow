# --- START OF FILE deepseek_ollama_client.py ---

import logging

from langchain_core.messages import HumanMessage  # same module you used for AIMessage
from langchain_ollama import ChatOllama  # make sure you have `pip install -U langchain-ollama`

logger = logging.getLogger(__name__)


class DeepseekOllamaClient:
    """
    Wrapper for models running locally via Ollama (e.g. Deepseek),
    with separate 'reasoning' and 'concept' models.
    """

    def __init__(
            self,
            reasoning_model: str = "qwq",
            concept_model: str = "deepseek-coder-v2",
            default_model_type: str = "reasoning",  # either "reasoning" or "concept"
            base_url: str = "http://localhost:11434",
            verbose: bool = False,
    ):
        logger.info(
            "Initializing DeepseekOllamaClient "
            "(reasoning=%s, concept=%s, default=%s, url=%s)",
            reasoning_model, concept_model, default_model_type, base_url,
        )

        if default_model_type not in {"reasoning", "concept"}:
            raise ValueError("default_model_type must be 'reasoning' or 'concept'")

        self.reasoning_model_name = reasoning_model
        self.concept_model_name = concept_model
        self.ollama_base_url = base_url
        self.default_model_type = default_model_type

        try:
            self.reasoning_llm = ChatOllama(
                model=self.reasoning_model_name,
                base_url=self.ollama_base_url,
                verbose=verbose,
            )
            logger.info("Loaded reasoning model '%s'", reasoning_model)

            self.concept_llm = ChatOllama(
                model=self.concept_model_name,
                base_url=self.ollama_base_url,
                verbose=verbose,
            )
            logger.info("Loaded concept model '%s'", concept_model)

        except Exception as e:
            logger.error(
                "Failed to initialize Ollama models. Is Ollama running and are the models pulled?",
                exc_info=True,
            )
            raise RuntimeError(f"Ollama init failed: {e}") from e

    def get_llm(self, model_type: str = None) -> ChatOllama:
        """
        Return the appropriate ChatOllama (reasoning vs concept).
        """
        kind = model_type or self.default_model_type
        return self.concept_llm if kind == "concept" else self.reasoning_llm

    def __call__(self, prompt: str, model_type: str = None) -> str:
        """
        Send a single-prompt to Ollama via invoke([...]) and return its .content.
        """
        kind = model_type or self.default_model_type
        llm = self.get_llm(kind)
        name = llm.model

        logger.info(
            "Calling Ollama (type=%s, model=%s): %s",
            kind, name, prompt[:150] + ("…" if len(prompt) > 150 else ""),
        )

        try:
            # invoke() expects a list of BaseMessage (HumanMessage, SystemMessage, etc)
            ai_msg = llm.invoke([HumanMessage(content=prompt)])
            # ai_msg is a BaseMessage with a .content field
            logger.debug("Ollama response: %r", ai_msg.content)
            return ai_msg.content

        except Exception as e:
            logger.error("Error while invoking Ollama '%s': %s", name, e, exc_info=True)
            return f"Error: could not get response from Ollama model '{name}'."


if __name__ == "__main__":
    # Make sure you have:
    #   pip install -U langchain-ollama
    #   ollama run deepseek-r1:7b
    #   ollama run qwq:32b
    #   ollama run deepseek-coder-v2:16b
    #   ollama list

    client = DeepseekOllamaClient(
        reasoning_model="deepseek-r1:7b",
        concept_model="deepseek-coder-v2:16b",
        default_model_type="reasoning",
        verbose=True,
    )

    print("--- Reasoning ---")
    # print(client("Write a Python function to compute factorial.", model_type="reasoning"))

    print("\n--- Concept ---")
    print(client("Explain recursion in simple terms.", model_type="concept"))
