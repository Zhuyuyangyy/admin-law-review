"""FastAPI application entry point"""
from fastapi import FastAPI
app = FastAPI(title="admin-law-review")
@app.get("/health")
async def health(): return {"status": "ok"}
