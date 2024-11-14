import asyncio
import configparser
import os
from typing import Optional, List, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from src.OPCUA import OPCUA
from src.Machine import Machine
from src.VectorDB import VectorDB
from src.Cache import Cache
from src.Frontend import Frontend
from src.RAG import RAG
from src.checkConfig import toBool, toInt, toString

# Import logging
from src.loggingConfig import logger

# Load config variables
config = configparser.ConfigParser()
config.read("config.ini")

configFastApiTLS = toBool(config["FastAPI"]["enable_tls"].strip('\"'))
configFastApiAddress = toString(config["FastAPI"]["ip_address"].strip('\"'))
configFastApiPort = toInt(config["FastAPI"]["port"].strip('\"'))

configCorsOrigins = toString(config["cors"]["allow_origins"].strip('\"'))
configCorsCredentials = toBool(config["cors"]["allow_credentials"].strip('\"'))
configCorsMethods = toString(config["cors"]["allow_methods"].strip('\"'))
configCorsHeaders = toString(config["cors"]["allow_headers"].strip('\"'))

configEmbeddingModel = toString(config["vectorDatabase"]["embedding_model"].strip('\"'))
configUseGPUEmbedding = toBool(config["vectorDatabase"]["use_gpu"].strip('\"'))

configOpcuaInterval = toInt(config["opcua"]["opcua_interval"].strip('\"'))

configUseLocalLLM = toBool(config["llm"]["use_local_LLM"].strip('\"'))
configFileName = toString(config["llm"]["llm_local_fileName"].strip('\"'))
configBatchSize = toInt(config["llm"]["llm_local_batchsize"].strip('\"'))
configCtxSize = toInt(config["llm"]["llm_local_ctxsize"].strip('\"'))
configGpuLayers = toInt(config["llm"]["llm_local_layers"].strip('\"'))
configModelName = toString(config["llm"]["llm_cloud_hoster"].strip('\"'))
configModelName += ": " + toString(config["llm"]["llm_cloud_model"].strip('\"'))
#opcua settings are different by machine, getting read below

configMachines = config.sections()[5:]

# Initialize FastAPI
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=configCorsOrigins.split(","),
    allow_credentials=configCorsCredentials,
    allow_methods=configCorsMethods.split(","),
    allow_headers=configCorsHeaders.split(","),
)

# SSL configuration
ssl_options = {}
if configFastApiTLS:
    ssl_keyfile = "./keys/privkey.pem"
    ssl_certfile = "./keys/fullchain.pem"
    ssl_options['ssl_keyfile'] = ssl_keyfile
    ssl_options['ssl_certfile'] = ssl_certfile
    logger.info("SSL encryption is enabled.")
else:
    logger.info("SSL encryption is disabled.")

def selectLLM(
    useLocaLlm: bool,
    fileName: str,
    batchSize: int,
    ctxSize: int,
    gpuLayers: int,
    modelName: str
) -> Any:
    """
    Select and initialize the appropriate LLM based on the configuration.
    """
    if useLocaLlm:
        logger.info("Creating local LLM instance")
        from src.LocalLLM import LocalLLM
        llm_obj = LocalLLM(fileName, batchSize, ctxSize, gpuLayers)
        llm_obj.load()
    else:
        logger.info("Creating cloud LLM instance")
        from src.WebLLM import WebLLM
        llm_obj = WebLLM()
        llm_obj.setupCloudLLM(modelName)
    
    return llm_obj.llm

# Initialize OPC UA, LLM, and VectorDB
opcua = OPCUA()
llm = selectLLM(configUseLocalLLM, configFileName, configBatchSize, configCtxSize, configGpuLayers, configModelName)
vdb = VectorDB(configEmbeddingModel, configUseGPUEmbedding)
cache = Cache()

rag = RAG(llm, vdb, cache)
frontend = Frontend(app, rag)
allmachines: List[Machine] = []

# Pydantic model for incoming RAG queries
class RAGQuery(BaseModel):
    query: str

async def main() -> None:
    """
    Main function to initialize machines and subscriptions.
    """
    stop_event = asyncio.Event()

   # Initialize machine instances with their own handlers
    for machine in configMachines:
        machineType = toString(config[machine]["type"].strip('\"'))
        machineIpAddress = toString(config[machine]["ip_address"].strip('\"'))
        machinePort = toInt(config[machine]["port"].strip('\"'))
        machineFromNodeID = toString(config[machine]["from_node_id"].strip('\"'))
        machineToNodeID = toString(config[machine]["from_node_id"].strip('\"'))
        machineVdbName = toString(config[machine]["vdb_name"].strip('\"'))
        machineAddPrompt = toString(config[machine]["additional_prompt"].strip('\"'))
        machineOpcUseCert = toBool(config[machine]["opcua_use_certificate"].strip('\"'))
        machineOpcUser = toString(config[machine]["opcua_username"].strip('\"'))
        machineOpcPass = toString(config[machine]["opcua_password"].strip('\"'))

        machineObj = Machine(
            machine,
            machineType,
            f"{machineIpAddress}:{machinePort}",
            machineFromNodeID,
            machineToNodeID,
            machineVdbName,
            machineAddPrompt,
            machineOpcUseCert,
            machineOpcUser,
            machineOpcPass,
            rag,
            frontend
        )
        allmachines.append(machineObj)

    # Create OPC UA subscriptions for each machine
    try:
        for machine in allmachines:
            await opcua.createSubscription(machine, configOpcuaInterval)
            await frontend.createTenantInstance(machine.name, "")
        await stop_event.wait()
    except KeyboardInterrupt:
        logger.info("Program interrupted, shutting down.")
    finally:
        # Perform any necessary cleanup here
        pass

@app.websocket("/ws")
async def websocketEndpoint(websocket: WebSocket, machineName: str = Query(...)) -> None:
    """
    WebSocket connection for tenant-specific communication.
    """
    if not machineName:
        logger.error("No tenant ID provided")
        await websocket.close(code=1008)  # Policy Violation close code
        return
    
    logger.info(f"WebSocket connection attempt for machineName: {machineName}")
    machineType = next((machine.type for machine in allmachines if machine.name == machineName), None)
    await frontend.connect(machineName, websocket)
    try:
        while True:
            await frontend.receiveMessage(machineName, machineType, websocket)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for machineName: {machineName}")
        frontend.disconnect(machineName, websocket)

@app.get("/{machineName}")
@app.get("/{machineName}/{file_path:path}")
async def serveTenantContent(machineName: str, filePath: Optional[str] = "") -> FileResponse:
    """
    Route to serve the tenant-specific HTML file.
    """
    if filePath == "favicon.ico":
        faviconPath = "path/to/your/favicon.ico"  # Update this path
        if os.path.exists(faviconPath):
            return FileResponse(faviconPath)
        raise HTTPException(status_code=404, detail="Favicon not found")
    
    basePath = os.path.join("tenants", machineName)
    
    if not filePath or filePath == "index.html":
        return frontend.serveHtml(machineName)
    
    fullPath = os.path.join(basePath, filePath)
    if os.path.exists(fullPath) and not os.path.isdir(fullPath):
        return FileResponse(fullPath)
    
    raise HTTPException(status_code=404, detail="File not found")

@app.on_event("startup")
async def startupEvent() -> None:
    """
    Startup event to ensure the main function runs before handling requests.
    """
    asyncio.create_task(main())

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        app,
        host=configFastApiAddress,
        port=int(configFastApiPort),
        **ssl_options
    )
