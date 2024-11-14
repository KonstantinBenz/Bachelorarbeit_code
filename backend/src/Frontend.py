import os
import shutil
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, List, Any
from src.RAG import RAG
from fastapi import FastAPI

# Import logging
from src.loggingConfig import logger

class Frontend:
    def __init__(self, app: FastAPI, rag: RAG) -> None:
        """
        Initialize the Frontend instance with the app and RAG (Retriever-Augmented Generation) instance.
        
        :param app: FastAPI app instance to add routes and mount static files.
        :param rag: An instance of the RAG class for processing queries.
        """
        self.tenants: Dict[str, List[WebSocket]] = {}
        self.app: FastAPI = app
        self.rag: RAG = rag

        # Mount the static directory for tenant-specific HTML files
        self.app.mount("/tenants", StaticFiles(directory="tenants"), name="tenants")
        logger.info("Frontend initialized and tenants directory mounted.")

    async def createTenantInstance(self, machineName: str, initialData: str) -> None:
        """
        Create a tenant-specific frontend instance by copying and modifying an HTML template.
        
        :param machineName: Name of the machine (tenant) for which the HTML is being created.
        :param initialData: Data to be inserted into the tenant's HTML file.
        """
        logger.info(f"Creating tenant-specific frontend instance for {machineName}")
        
        tenantDir = os.path.join("tenants", machineName)
        os.makedirs(tenantDir, exist_ok=True)

        srcHtmlPath = "./frontend/index.html"
        srcLogoPath = "./frontend/img/logo.png"
        destHtmlPath = os.path.join(tenantDir, "index.html")
        destLogoPath = os.path.join(tenantDir, "logo.png")
        
        shutil.copyfile(srcHtmlPath, destHtmlPath)
        shutil.copyfile(srcLogoPath, destLogoPath)

        with open(destHtmlPath, "r") as file:
            htmlContent = file.read()

        # Replace placeholders in the HTML content
        htmlContent = htmlContent.replace("{{INITIAL_DATA}}", initialData)
        htmlContent = htmlContent.replace("{{TENANT_ID}}", machineName)

        with open(destHtmlPath, "w") as file:
            file.write(htmlContent)

        logger.info(f"Tenant HTML created at {destHtmlPath} for {machineName}")

    async def connect(self, machineName: str, websocket: WebSocket) -> None:
        """
        Handle new WebSocket connections for a tenant.
        
        :param machineName: Name of the machine (tenant) connecting via WebSocket.
        :param websocket: WebSocket instance for the connection.
        """
        await websocket.accept()

        if machineName not in self.tenants:
            self.tenants[machineName] = []

        self.tenants[machineName].append(websocket)
        logger.info(f"New WebSocket connection for tenant {machineName}")

    def disconnect(self, machineName: str, websocket: WebSocket) -> None:
        """
        Handle disconnection of a WebSocket for a given tenant.
        
        :param machineName: Name of the machine (tenant) disconnecting.
        :param websocket: WebSocket instance for the disconnection.
        """
        if machineName in self.tenants and websocket in self.tenants[machineName]:
            self.tenants[machineName].remove(websocket)
            if not self.tenants[machineName]:
                del self.tenants[machineName]
            logger.info(f"WebSocket disconnected for tenant {machineName}")
        else:
            logger.warning(f"WebSocket disconnect attempted for non-existent tenant {machineName}")

    async def receiveMessage(self, machineName: str, machineType: Any, websocket: WebSocket) -> None:
        """
        Receive a message from a WebSocket connection and send a response.
        
        :param machineName: Name of the machine (tenant) sending the message.
        :param machineType: Type of machine (tenant) to query.
        :param websocket: WebSocket instance for the connection.
        """
        try:
            data = await websocket.receive_text()
            logger.info(f"Received message from tenant {machineName}: {data}")

            response = await self.rag.retrieve(machineType, machineName, data)
            logger.info(f"Sending response to tenant {machineName}: {response}")
            await self.sendMessage(machineName, response)
        except WebSocketDisconnect:
            self.disconnect(machineName, websocket)
            logger.warning(f"WebSocket disconnected unexpectedly for tenant {machineName}")

    async def sendMessage(self, machineName: str, message: str) -> None:
        """
        Send a message to all connected WebSockets of a given tenant.
        
        :param machineName: Name of the machine (tenant) to which the message will be sent.
        :param message: Message content to be sent.
        """
        if machineName in self.tenants:
            for websocket in self.tenants[machineName]:
                await websocket.send_text(message)
            logger.info(f"Message sent to tenant {machineName}: {message}")
        else:
            logger.warning(f"No WebSockets found for tenant {machineName}")

    def serveHtml(self, machineName: str) -> HTMLResponse:
        """
        Serve the HTML file for a tenant's frontend.
        
        :param machineName: Name of the machine (tenant) whose HTML will be served.
        :return: HTMLResponse containing the tenant's HTML content.
        :raises HTTPException: If the HTML file for the tenant does not exist.
        """
        tenantHtmlPath = os.path.join("tenants", machineName, "index.html")
        
        if not os.path.exists(tenantHtmlPath):
            logger.error(f"HTML file for tenant {machineName} not found at {tenantHtmlPath}")
            raise HTTPException(status_code=404, detail=f"HTML file for tenant {machineName} not found")
        
        with open(tenantHtmlPath, "r") as file:
            content = file.read()
        
        logger.info(f"Serving HTML file for tenant {machineName}")
        return HTMLResponse(content=content)
