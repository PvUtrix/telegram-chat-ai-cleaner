"""
FastAPI backend for Telegram Chat Analyzer
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ...core import TelegramAnalyzer
from ...config.config_manager import ConfigManager
from ...processors.batch_processor import BatchProcessor
from ...processors.file_manager import FileManager


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Global instances
config = None
analyzer = None
file_manager = None
batch_processor = None

# WebSocket connections for progress updates
active_connections: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global config, analyzer, file_manager, batch_processor

    # Startup
    config = ConfigManager()
    analyzer = TelegramAnalyzer()
    file_manager = FileManager(config)
    batch_processor = BatchProcessor(analyzer)

    logger.info("Telegram Chat Analyzer backend started")

    yield

    # Shutdown
    logger.info("Telegram Chat Analyzer backend shutting down")


# Create FastAPI app
app = FastAPI(
    title="Telegram Chat Analyzer API",
    description="API for cleaning, analyzing, and vectorizing Telegram chat exports",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API
class CleanRequest(BaseModel):
    approach: str = Field("privacy", description="Cleaning approach")
    level: int = Field(2, description="Cleaning level (1-3)")
    output_format: str = Field("text", description="Output format")


class AnalyzeRequest(BaseModel):
    prompt: Optional[str] = Field(None, description="Custom analysis prompt")
    template: Optional[str] = Field(None, description="Prompt template name")
    provider: Optional[str] = Field(None, description="LLM provider")
    model: Optional[str] = Field(None, description="LLM model")
    stream: bool = Field(False, description="Stream response")


class VectorizeRequest(BaseModel):
    provider: Optional[str] = Field(None, description="Embedding provider")
    model: Optional[str] = Field(None, description="Embedding model")
    chunk_strategy: str = Field("overlap", description="Text chunking strategy")
    chunk_size: Optional[int] = Field(None, description="Text chunk size")


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(10, description="Maximum results")
    provider: Optional[str] = Field(None, description="Embedding provider")
    metadata_filter: Optional[Dict[str, Any]] = Field(None, description="Metadata filter")


class ConfigUpdate(BaseModel):
    key: str = Field(..., description="Configuration key")
    value: Any = Field(..., description="Configuration value")


class BatchProcessRequest(BaseModel):
    approach: str = Field("privacy", description="Cleaning approach")
    level: int = Field(2, description="Cleaning level (1-3)")
    output_format: str = Field("text", description="Output format")


# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to websocket: {e}")
                self.disconnect(connection)


manager = ConnectionManager()


# API Routes
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Telegram Chat Analyzer API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "config_loaded": config is not None,
        "analyzer_ready": analyzer is not None
    }


@app.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    clean_options: Optional[CleanRequest] = None
):
    """Upload and optionally process a Telegram JSON file"""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are supported")

    try:
        # Read file content
        content = await file.read()
        json_data = content.decode('utf-8')

        # Save to input directory
        input_path = file_manager.get_input_dir() / file.filename
        with open(input_path, 'w', encoding='utf-8') as f:
            f.write(json_data)

        result = {
            "filename": file.filename,
            "saved_to": str(input_path),
            "file_size": len(content)
        }

        # Optionally start cleaning process
        if clean_options:
            background_tasks.add_task(
                process_file_background,
                str(input_path),
                clean_options.dict()
            )
            result["processing_started"] = True

        return result

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/clean/{filename}")
async def clean_file(filename: str, options: CleanRequest):
    """Clean a specific file"""
    input_path = file_manager.get_input_dir() / filename

    if not input_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        cleaned_data = analyzer.clean(
            input_file=str(input_path),
            approach=options.approach,
            level=options.level,
            output_format=options.output_format
        )

        # Generate output path and save
        output_path = file_manager.generate_output_path(
            str(input_path), options.approach, options.level, options.output_format
        )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_data)

        return {
            "input_file": filename,
            "output_file": output_path,
            "approach": options.approach,
            "level": options.level,
            "format": options.output_format,
            "size": len(cleaned_data)
        }

    except Exception as e:
        logger.error(f"Cleaning failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleaning failed: {str(e)}")


@app.post("/analyze")
async def analyze_text(request: AnalyzeRequest):
    """Analyze text with LLM"""
    try:
        if not request.prompt and not request.template:
            raise HTTPException(status_code=400, detail="Either prompt or template must be provided")

        # Get prompt
        prompt = request.prompt
        if request.template:
            from ...llm.templates.default_prompts import get_prompt_template
            prompt = get_prompt_template(request.template)

        # For demo purposes, we'll analyze a simple text
        # In production, you'd want to accept text input
        demo_text = "This is a demo chat message for analysis."

        result = await analyzer.analyze(
            input_data=demo_text,
            prompt=prompt,
            provider=request.provider,
            model=request.model
        )

        return {
            "result": result,
            "provider": request.provider or "default",
            "model": request.model or "default",
            "length": len(result)
        }

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/vectorize/{filename}")
async def vectorize_file(filename: str, options: VectorizeRequest):
    """Create embeddings for a file"""
    input_path = file_manager.get_input_dir() / filename

    if not input_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # Read file content
        with open(input_path, 'r', encoding='utf-8') as f:
            text_data = f.read()

        # Vectorize
        result = await analyzer.vectorize(
            input_data=text_data,
            provider=options.provider,
            model=options.model,
            metadata={"source_file": filename},
            chunking_strategy=options.chunk_strategy
        )

        return result

    except Exception as e:
        logger.error(f"Vectorization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Vectorization failed: {str(e)}")


@app.post("/search")
async def search_vectors(request: SearchRequest):
    """Search vector database"""
    try:
        results = await analyzer.search_vectors(
            query=request.query,
            limit=request.limit,
            provider=request.provider,
            metadata_filter=request.metadata_filter
        )

        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/batch-process")
async def batch_process_files(background_tasks: BackgroundTasks, options: BatchProcessRequest):
    """Process all files in input directory"""
    try:
        background_tasks.add_task(
            batch_process_background,
            options.dict()
        )

        return {
            "message": "Batch processing started",
            "options": options.dict()
        }

    except Exception as e:
        logger.error(f"Batch process failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch process failed: {str(e)}")


@app.get("/files")
async def list_files():
    """List files in input and output directories"""
    try:
        input_files = [f.name for f in file_manager.list_input_files()]
        output_files = []

        # Get output files from all subdirectories
        for subdir in file_manager.get_output_dir().iterdir():
            if subdir.is_dir():
                output_files.extend([f"{subdir.name}/{f.name}" for f in subdir.glob("*")])

        return {
            "input_files": input_files,
            "output_files": output_files
        }

    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@app.get("/config")
async def get_config():
    """Get current configuration (non-sensitive)"""
    try:
        config_data = config.get_all()

        # Remove sensitive information
        safe_config = {}
        for key, value in config_data.items():
            if any(sensitive in key.lower() for sensitive in ['key', 'secret', 'password']):
                safe_config[key] = "••••••••" if value else None
            else:
                safe_config[key] = value

        return safe_config

    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@app.post("/config")
async def update_config(update: ConfigUpdate):
    """Update configuration"""
    try:
        config.set(update.key, update.value)
        config.save_to_env()

        return {
            "message": f"Configuration updated: {update.key}",
            "key": update.key
        }

    except Exception as e:
        logger.error(f"Config update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Config update failed: {str(e)}")


@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for progress updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for testing
            await websocket.send_text(f"Received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Background task functions
async def process_file_background(file_path: str, options: Dict[str, Any]):
    """Background task to process a single file"""
    try:
        await manager.broadcast({
            "type": "processing_started",
            "file": file_path,
            "options": options
        })

        # Process file
        cleaned_data = analyzer.clean(
            input_file=file_path,
            **options
        )

        # Save result
        output_path = file_manager.generate_output_path(
            file_path, options["approach"], options["level"], options["output_format"]
        )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_data)

        await manager.broadcast({
            "type": "processing_completed",
            "file": file_path,
            "output": output_path,
            "size": len(cleaned_data)
        })

    except Exception as e:
        await manager.broadcast({
            "type": "processing_failed",
            "file": file_path,
            "error": str(e)
        })


async def batch_process_background(options: Dict[str, Any]):
    """Background task for batch processing"""
    try:
        await manager.broadcast({
            "type": "batch_started",
            "options": options
        })

        # Process all files
        results = batch_processor.process_directory(
            input_dir=file_manager.get_input_dir(),
            output_dir=file_manager.get_output_dir(options["approach"], options["level"]),
            **options
        )

        await manager.broadcast({
            "type": "batch_completed",
            "results": results,
            "total_files": len(results)
        })

    except Exception as e:
        await manager.broadcast({
            "type": "batch_failed",
            "error": str(e)
        })


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

