from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="GradeSense API", version="0.1.0")

# CORS: support single or comma-separated origins via CORS_ORIGIN
origins_env = os.getenv("CORS_ORIGIN", "*")
origins = [o.strip() for o in origins_env.split(",")] if origins_env else ["*"]
allow_all = "*" in origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/version")
def version():
    return {"name": "GradeSense API", "version": app.version}

# Mount API routes
from app.api import router as api_router  # noqa: E402
app.include_router(api_router, prefix="/api")
