from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.datasets import router as datasets_router
from app.config import ensure_data_directories


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_data_directories()
    yield


app = FastAPI(
    title="Data Analyst MCP",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(datasets_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "data-analyst-mcp",
    }