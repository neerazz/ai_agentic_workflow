import logging

from langchain_community.chat_models import ChatPerplexity

from src.ai_agentic_workflow.utils.env_reader import get_env_variable

logger = logging.getLogger(__name__)

class DualModelPerplexityClient:
    """
    Wrapper for Perplexity AI with reasoning/concept models and facade.
    """
    def __init__(self,
                 reasoning_model: str = "perplexity-2",
                 concept_model: str   = "perplexity-lite",
                 default_model: str   = "reasoning"):
        logger.info(
            "Initializing (reasoning_model=%s, concept_model=%s, default_model=%s)",
            reasoning_model, concept_model, default_model
        )
        api_key = get_env_variable("PERPLEXITY_API_KEY")
        self.reasoning_llm = ChatPerplexity(pplx_api_key=api_key, model=reasoning_model)
        self.concept_llm = ChatPerplexity(pplx_api_key=api_key, model=concept_model)
        self.default_model = default_model

    def call_reasoning(self, prompt: str) -> str:
        return self.reasoning_llm(prompt)

    def call_concept(self, prompt: str) -> str:
        return self.concept_llm(prompt)

    def get_llm(self, model_type: str = None):
        chosen = model_type or self.default_model
        llm = self.concept_llm if chosen == "concept" else self.reasoning_llm
        logger.debug("(model_type=%s) -> %s", model_type, chosen)
        return llm

    def __call__(self, prompt: str, model_type: str = None) -> str:
        chosen = model_type or self.default_model
        logger.info(
            "(model_type=%s): prompt=%s",
            chosen, prompt
        )
        return self.get_llm(model_type)(prompt)
