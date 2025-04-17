import logging

from langchain_community.chat_models import ChatOpenAI

from src.ai_agentic_workflow.utils.env_reader import get_env_variable

logger = logging.getLogger(__name__)


class DualModelGroqClient:
    """
    Wrapper for GROQ that maintains reasoning and concept LLMs with facade.
    """

    def __init__(self,
                 reasoning_model: str = "gpt-4",
                 concept_model: str = "gpt-3.5-turbo",
                 default_model: str = "reasoning"):
        logger.info(
            "Initializing (reasoning_model=%s, concept_model=%s, default_model=%s)",
            reasoning_model, concept_model, default_model
        )
        api_key = get_env_variable("GROQ_API_KEY")
        self.reasoning_llm = ChatOpenAI(openai_api_key=api_key, model_name=reasoning_model)
        self.concept_llm = ChatOpenAI(openai_api_key=api_key, model_name=concept_model)
        self.default_model = default_model

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
