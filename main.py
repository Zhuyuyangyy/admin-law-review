"""FastAPI application entry point for admin-law-review."""
import sys
from pathlib import Path

# Ensure backend is on the Python path so `app.*` imports work
_backend = str(Path(__file__).resolve().parent / "backend")
if _backend not in sys.path:
    sys.path.insert(0, _backend)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="行政执法案卷合规评查系统",
    description="基于证据链闭环的行政执法案卷合规评查系统，支持裁量基准匹配、风险熵分级评估和同案相似度检索。",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


# Mount the v1 API router (review_case, consistency, procedure, etc.)
try:
    from app.main import router as v1_router
    app.include_router(v1_router)
except ImportError:
    pass

# Mount the core API router (upload, analyze, evidence, discretion, etc.)
try:
    from app.api.routes import router as core_router
    app.include_router(core_router, prefix="/api")
except ImportError:
    pass
