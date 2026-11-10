import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import HOST, PORT, DEBUG
from database import init_db
from routes import converse_ws, converse_rest, sessions

# Configure logging
logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("vani_ai")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database tables
    logger.info("Initializing SQLite database tables...")
    init_db()
    logger.info("Vani AI Voice Assistant Engine online.")
    yield
    # Shutdown
    logger.info("Vani AI Engine shutting down...")

app = FastAPI(
    title="Vani AI — Multilingual Voice Assistant Engine",
    description="Asynchronous voice assistant backend with Sarvam AI STT/TTS, Google Gemini Flash reasoning, and Dual-Layer Guardrails.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Route Handlers
app.include_router(converse_ws.router)
app.include_router(converse_rest.router)
app.include_router(sessions.router)

@app.get("/")
def index():
    return {
        "service": "Vani AI Engine",
        "status": "active",
        "docs_url": "/docs",
        "ws_endpoint": "/ws/converse",
        "rest_endpoint": "/api/converse"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=DEBUG)
