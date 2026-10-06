import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fingerprint import compute_fingerprint
from optimize import optimize_scene
from schemas import FingerprintRequest, FingerprintResponse, OptimizeRequest, OptimizeResponse


def cors_origins() -> list[str]:
    value = os.getenv("LAYOUT_DNA_CORS_ORIGINS", "http://localhost:5241,https://localhost:5241")
    return [origin.strip() for origin in value.split(",") if origin.strip()]


app = FastAPI(
    title="LayoutDNA Solver",
    version="0.1.0",
    description="Deterministic vertical skeleton; not the final differentiable optimizer.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "solver": "deterministic-placeholder", "version": "0.1.0"}


@app.post("/api/v1/fingerprint", response_model=FingerprintResponse)
def fingerprint(request: FingerprintRequest) -> FingerprintResponse:
    return compute_fingerprint(request.scene)


@app.post("/api/v1/optimize", response_model=OptimizeResponse)
def optimize(request: OptimizeRequest) -> OptimizeResponse:
    return optimize_scene(request)
