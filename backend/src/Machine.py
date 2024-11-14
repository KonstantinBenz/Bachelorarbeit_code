from typing import Any
from src.RAG import RAG
from src.Frontend import Frontend


# Import logging
from src.loggingConfig import logger

class Machine:
    def __init__(
        self, 
        name: str, 
        nameVdb: str, 
        ipAddress: str, 
        fromNodeID: str, 
        toNodeID: str, 
        vdbType: str, 
        additionalPrompt: str, 
        machineOpcUseCert : bool,
        machineOpcUser: str,
        machineOpcPass: str,
        rag: RAG,
        frontend: Frontend
    ) -> None:
        """
        Initialize the Machine instance with its configuration parameters.

        :param name: Name of the machine.
        :param nameVdb: Type of the machine in the VDB system.
        :param ipAddress: IP address of the machine.
        :param fromNodeID: Node identifier of the machine input in the system.
        :param toNodeID: Node identifier of the machine output in the system.
        :param vdbType: Type of the VDB (virtual database) used.
        :param additionalPrompt: Any additional information to be added in prompts.
        :param rag: Retriever-Augmented Generation (RAG) instance to handle queries.
        :param frontend: Frontend instance to handle tenant-specific interactions.
        """
        self.name: str = name
        self.type: str = nameVdb
        self.ipAddress: str = ipAddress
        self.fromNodeID: str = fromNodeID
        self.toNodeID: str = toNodeID
        self.vdbType: str = vdbType
        self.additionalPrompt: str = additionalPrompt
        self.machineOpcUseCert : bool = machineOpcUseCert
        self.machineOpcUser: str = machineOpcUser
        self.machineOpcPass: str = machineOpcPass
        self.rag: RAG = rag
        self.frontend: Frontend = frontend
        logger.info(f"Machine {self.name} (type: {self.type}) initialized with IP {self.ipAddress} and node ID {self.fromNodeID}.")

    async def datachange_notification(self, node: Any, val: str, data: Any) -> None:
        """
        Handle data change notifications for the machine.

        :param node: The node where the data change occurred.
        :param val: The new value after the data change.
        :param data: Additional data associated with the change.
        :return: The response from the RAG model after processing the data change.
        """
        logger.info(f"Data change detected on machine {self.name} (type: {self.type}) on node {node}: {val}")

        # Retrieve the response from the RAG model
        try:
            response = await self.rag.retrieve(self.type, self.name, val)
            logger.info(f"RAG response for machine {self.name} (node {node}): {response}")
        except Exception as e:
            logger.error(f"Error retrieving RAG response for machine {self.name}: {e}")
            return f"Error processing data change for {self.name}"

        # Create a tenant instance and send the message to the frontend
        try:
            await self.frontend.createTenantInstance(self.name, response)
            await self.frontend.sendMessage(self.name, response)
            instanceURL = f"https://localhost:8000/{self.name}"
            logger.info(f"Frontend instance created for tenant {self.name} at {instanceURL}")
        except Exception as e:
            logger.error(f"Error creating tenant instance or sending message for {self.name}: {e}")
            return f"Error creating frontend for {self.name}"

        # Send URL of Tenant to opcua
        try:
            pass
        except Exception as e:
            pass

