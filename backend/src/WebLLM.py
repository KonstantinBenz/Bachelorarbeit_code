import os
from typing import Optional
from src.loggingConfig import logger

class WebLLM:
    def __init__(self) -> None:
        """
        Initialize the WebLLM instance.
        """
        self.llm: Optional[object] = None  # Type is Optional because it will be set later

    def setupCloudLLM(self, providerAndModel: str) -> None:
        """
        Setup the cloud-based LLM based on the provided provider and model.

        :param providerAndModel: String containing provider and model separated by ': '
        """
        try:
            provider, model = map(str.strip, providerAndModel.split(":"))
            provider = provider.lower()
            model = model.lower()

            logger.info(f"Setting up LLM with provider: {provider}, model: {model}")
            
            match provider:
                case "groq":
                    self.setupGroqLLM(model)
                case "openai":
                    self.setupOpenAILLM(model)
                case "cohere":
                    self.setupCohereLLM(model)
                case _:
                    logger.error(f"No valid model selected for provider {provider}.")
                    print("No valid model selected")
        except Exception as e:
            logger.error(f"Failed to setup cloud LLM: {e}")
            print(f"Error setting up LLM: {e}")

    def setupGroqLLM(self, modelname: str) -> None:
        """
        Setup the Groq LLM with the provided model name.
        """
        try:
            from langchain_groq import ChatGroq
            APIKey = os.getenv("GROQ_API_KEY")
            if APIKey is None:
                raise ValueError("GROQ API key not set in environment variables.")
            
            self.llm = ChatGroq(model=modelname, api_key=APIKey, temperature=1)
            logger.info(f"Groq LLM set up successfully with model {modelname}.")
        except Exception as e:
            logger.error(f"Failed to setup Groq LLM: {e}")
    
    def setupCohereLLM(self, modelname: str) -> None:
        """
        Setup the Cohere LLM with the provided model name.
        """
        try:
            from langchain_cohere import ChatCohere
            APIKey = os.getenv("COHERE_API_KEY")
            if APIKey is None:
                raise ValueError("Cohere API key not set in environment variables.")
            
            self.llm = ChatCohere(model=modelname, api_key=APIKey, temperature=1)
            logger.info(f"Cohere LLM set up successfully with model {modelname}.")
        except Exception as e:
            logger.error(f"Failed to setup Cohere LLM: {e}")

    def setupOpenAILLM(self, modelname: str) -> None:
        """
        Setup the OpenAI LLM with the provided model name.
        """
        try:
            from langchain_openai import ChatOpenAI
            APIKey = os.getenv("OPENAI_API_KEY")
            if APIKey is None:
                raise ValueError("OpenAI API key not set in environment variables.")
            
            self.llm = ChatOpenAI(model=modelname, api_key=APIKey, temperature=1)
            logger.info(f"OpenAI LLM set up successfully with model {modelname}.")
        except Exception as e:
            logger.error(f"Failed to setup OpenAI LLM: {e}")
