from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from typing import Optional
from src.loggingConfig import logger

class VectorDB:
    def __init__(self, embeddingModel: str, useGPU: bool) -> None:
        """
        Initialize the VectorDB instance with the necessary embeddings and model configuration.
        """
        self.vdb: Optional[FAISS] = None  # Optional, as it may be None before loading
        self.loadedVDBName: Optional[str] = None
        device = "cuda" if useGPU else "cpu"  # Use ternary expression for device selection
        
        # Initialize embeddings
        self.embeddings = HuggingFaceBgeEmbeddings(
            model_name=embeddingModel, 
            model_kwargs={"device": device}, 
            encode_kwargs={"normalize_embeddings": True}
        )
        logger.info(f"VectorDB initialized with model {embeddingModel} on {device}.")

    def loadVDB(self, dbName: str) -> None:
        """
        Load the Vector Database (VDB) from a local FAISS index.

        :param dbName: The name of the database to load.
        """
        try:
            # Load the FAISS vector store from the specified directory
            self.vdb = FAISS.load_local(
                "data/" + dbName, 
                self.embeddings,
                allow_dangerous_deserialization=True  # Set to True due to FAISS's serialization behavior
            )
            self.loadedVDBName = dbName
            logger.info(f"Loaded vector database {dbName} successfully.")
        except Exception as e:
            logger.error(f"Failed to load vector database {dbName}: {e}")
            self.vdb = None
            self.loadedVDBName = None
