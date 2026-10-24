from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.dependencies import lifespan, get_settings
from app.api.routes import conversations, research, health, sessions, chat


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    print(f"Starting Research Assistant API")
    print(f"LLM Provider: {settings.llm_provider}")
    print(f"Database: {settings.database_url}")
    yield
    # Shutdown
    print("Shutting down Research Assistant API")


app = FastAPI(
    title="Evidence-Grounded Research Assistant API",
    description="API for autonomous multi-paper literature investigation",
    version="1.0.0",
    lifespan=app_lifespan
)

# CORS configuration for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api prefix
app.include_router(health.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(research.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "Evidence-Grounded Research Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }