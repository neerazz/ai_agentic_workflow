import logging

from langchain_community.chat_models import ChatPerplexity

from src.ai_agentic_workflow.utils.env_reader import get_env_variable

logger = logging.getLogger(__name__)

class DualModelPerplexityClient:
    """
    Wrapper for Perplexity AI with reasoning/concept models and facade.
    """

    def __init__(self,
                 reasoning_model: str = "sonar-pro",  # Default should match what's used in workflow
                 concept_model: str = "sonar",  # Default should match what's used in workflow
                 default_model: str = "reasoning"):
        logger.info(
            "Initializing DualModelPerplexityClient with reasoning_model=%s, concept_model=%s, default_model=%s",
            reasoning_model, concept_model, default_model
        )
        api_key = get_env_variable("PERPLEXITY_API_KEY")

        # FIX: Prefix model names with 'perplexity/' as LiteLLM expects for Perplexity models.
        # This resolves the "LLM provider you are trying to call. You passed model=sonar-pro" error.
        self.reasoning_llm = ChatPerplexity(pplx_api_key=api_key, model=f"perplexity/{reasoning_model}")
        self.concept_llm = ChatPerplexity(pplx_api_key=api_key, model=f"perplexity/{concept_model}")
        self.default_model = default_model
        logger.debug(
            f"Perplexity clients initialized: reasoning_llm model='perplexity/{reasoning_model}', concept_llm model='perplexity/{concept_model}'")

    def call_reasoning(self, prompt: str) -> str:
        """Calls the reasoning model with the given prompt."""
        logger.debug(f"Calling Perplexity reasoning model with prompt: {prompt[:100]}...")
        return self.reasoning_llm.invoke(prompt)  # Use .invoke() for LangChain LLMs

    def call_concept(self, prompt: str) -> str:
        """Calls the concept model with the given prompt."""
        logger.debug(f"Calling Perplexity concept model with prompt: {prompt[:100]}...")
        return self.concept_llm.invoke(prompt)  # Use .invoke() for LangChain LLMs

    def get_llm(self, model_type: str = None):
        """
        Returns the appropriate LLM instance based on model_type.

        Args:
            model_type (str, optional): Type of model to get ('reasoning' or 'concept').
                                        Defaults to None, which uses default_model.
        Returns:
            ChatPerplexity: The selected LangChain ChatPerplexity LLM instance.
        """
        chosen = model_type or self.default_model
        llm = self.concept_llm if chosen == "concept" else self.reasoning_llm
        logger.debug(f"get_llm: requested model_type='{model_type}', chosen='{chosen}'")
        return llm

    def __call__(self, prompt: str, model_type: str = None) -> str:
        """
        Allows the client instance to be called directly like a function.

        Args:
            prompt (str): The input prompt for the LLM.
            model_type (str, optional): Type of model to use ('reasoning' or 'concept').
                                        Defaults to None, which uses default_model.
        Returns:
            str: The response from the LLM.
        """
        chosen = model_type or self.default_model
        logger.info(
            "PerplexityClient __call__ (model_type=%s): prompt=%s",
            chosen, prompt[:100]  # Log first 100 chars of prompt
        )
        return self.get_llm(model_type).invoke(prompt)  # Use .invoke() for LangChain LLMs
