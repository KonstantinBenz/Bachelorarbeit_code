from typing import Optional
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.llms import LlamaCpp
import gc
import torch

# Import logging
from src.loggingConfig import logger

class LocalLLM:
    def __init__(self, fileName: str, gpuLayers: int, batchSize: int, ctxSize: int) -> None:
        """
        Initialize the LocalLLM instance with configuration parameters.
        
        :param fileName: The name of the model file to be loaded.
        :param gpuLayers: The number of GPU layers to use in the model.
        :param batchSize: The batch size for inference.
        :param ctxSize: The context size for inference.
        """
        self.fileName: str = fileName
        self.gpuLayers: int = gpuLayers
        self.batchSize: int = batchSize
        self.ctxSize: int = ctxSize
        self.llm: Optional[LlamaCpp] = None  # Type hint for the LLM instance, initially None
        logger.info("Initialized LocalLLM instance with configuration parameters.")

    def load(self) -> None:
        """
        Load the LlamaCpp model with the specified parameters.
        """
        try:
            logger.info(f"Loading model: {self.fileName}")
            callbackManager = CallbackManager([StreamingStdOutCallbackHandler()])
            self.llm = LlamaCpp(
                modelPath=f"./models/{self.fileName}",
                gpuLayers=self.gpuLayers,
                batchSize=self.batchSize,
                ctxSize=self.ctxSize,
                callback_manager=callbackManager,
                verbose=True,
                stop=["<|im_end|>", "</s>"]
            )
            logger.info(f"Model {self.fileName} loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model {self.fileName}: {e}")
            self.llm = None  # Ensure llm is set to None in case of failure

    def unload(self) -> None:
        """
        Unload the LlamaCpp model and clear the memory.
        """
        try:
            if self.llm is not None:
                logger.info(f"Unloading model: {self.fileName}")
                gc.collect()
                torch.cuda.empty_cache()
                self.llm = None  # Set llm to None after unloading
                logger.info(f"Model {self.fileName} unloaded successfully and memory cleared.")
            else:
                logger.warning(f"No model loaded to unload for {self.fileName}.")
        except Exception as e:
            logger.error(f"Failed to unload model {self.fileName}: {e}")
