"""
OceanEmbed — FastAPI Backend.

Serves prediction and metadata endpoints.
Connects to the OceanEmbedEngine for real or DEMO inference.

Run:
    cd backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations


import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.inference.engine import OceanEmbedEngine
from src.data.grid import SIH_DEPTHS

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


# --- Engine (shared singleton) ------------------------------------------------
_engine: Optional[OceanEmbedEngine] = None


def get_engine() -> OceanEmbedEngine:
    global _engine
    if _engine is None:
        checkpoint = ROOT_DIR / "artifacts" / "checkpoints" / "ocean_embed_best.pt"
        _engine = OceanEmbedEngine(checkpoint_path=checkpoint)
    return _engine


# --- Lifespan Handler ---------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("OceanEmbed API starting up...")
    engine = get_engine()
    if engine.demo_mode:
        logger.warning(
            "[WARNING] DEMO / SYNTHETIC mode active. Predictions are NOT scientific results."
        )
    else:
        logger.info("Real model loaded. Scientific inference available.")
    yield
    logger.info("OceanEmbed API shutting down...")


# --- App init -----------------------------------------------------------------
app = FastAPI(
    title="OceanEmbed API",
    description=(
        "OceanEmbed: Continuous, Uncertainty-Aware and Missing-Data-Resilient "
        "Subsurface Ocean Temperature Reconstruction. "
        "SIH26066 | Ministry of Earth Sciences / INCOIS."
    ),
    version="1.0.0-dev",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS - allow frontend dev server
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic models ───────────────────────────────────────────────────────────

class PredictionRequest(BaseModel):
    lat: float = Field(..., ge=5.0, le=30.0, description="Latitude (5–30°N)")
    lon: float = Field(..., ge=45.0, le=105.0, description="Longitude (45–105°E)")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    depth: Optional[float] = Field(None, ge=0.0, le=1000.0, description="Depth in metres (0–1000)")
    depths: Optional[List[float]] = Field(None, description="List of depths to query")
    masks: Optional[Dict[str, bool]] = Field(
        None,
        description="Missing input flags: {'sst': True} means SST is missing"
    )


class ProfileRequest(BaseModel):
    lat: float = Field(..., ge=5.0, le=30.0)
    lon: float = Field(..., ge=45.0, le=105.0)
    date: str
    masks: Optional[Dict[str, bool]] = None


# ── Health endpoint ───────────────────────────────────────────────────────────

@app.get("/api/health", tags=["System"])
def health() -> Dict[str, Any]:
    """Health check endpoint."""
    engine = get_engine()
    return {
        "status": "ok",
        "demo_mode": engine.demo_mode,
        "data_type": "DEMO / SYNTHETIC" if engine.demo_mode else "REAL",
        "service": "OceanEmbed",
        "sih_id": "SIH26066",
    }


# ── Metadata endpoint ─────────────────────────────────────────────────────────

@app.get("/api/metadata", tags=["System"])
def metadata() -> Dict[str, Any]:
    """Return project and model metadata."""
    engine = get_engine()
    meta = engine.get_metadata()
    meta.update({
        "project": "OceanEmbed",
        "sih_id": "SIH26066",
        "organization": "Ministry of Earth Sciences / INCOIS",
        "description": (
            "Continuous, Uncertainty-Aware and Missing-Data-Resilient "
            "Subsurface Ocean Temperature Reconstruction"
        ),
        "inputs": ["sst", "sss", "ssh", "current_u", "current_v", "wind_u", "wind_v"],
        "target": "subsurface_temperature",
        "regions": ["Arabian Sea", "Bay of Bengal", "Open Ocean"],
    })
    return meta


# ── Depths endpoint ───────────────────────────────────────────────────────────

@app.get("/api/depths", tags=["System"])
def depths() -> Dict[str, Any]:
    """Return available standard depths."""
    return {
        "sih_standard_depths": SIH_DEPTHS,
        "depth_range": {"min": 0, "max": 1000, "unit": "m"},
        "continuous_depth_supported": True,
        "note": "Query any depth between 0 and 1000 m.",
    }


# ── Dates endpoint ────────────────────────────────────────────────────────────

@app.get("/api/dates", tags=["System"])
def dates() -> Dict[str, Any]:
    """Return available date information."""
    engine = get_engine()
    if engine.demo_mode:
        return {
            "demo": True,
            "data_type": "DEMO / SYNTHETIC",
            "note": "All dates accepted in demo mode.",
            "example_date": "2020-06-15",
        }
    return {
        "demo": False,
        "available_from": "RESULT NOT YET AVAILABLE",
        "note": "Real data availability depends on downloaded dataset.",
    }


# ── Prediction endpoint ────────────────────────────────────────────────────────

@app.get("/api/prediction", tags=["Inference"])
def get_prediction(
    lat: float = Query(..., ge=5.0, le=30.0, description="Latitude"),
    lon: float = Query(..., ge=45.0, le=105.0, description="Longitude"),
    date: str = Query(..., description="Date YYYY-MM-DD"),
    depth: Optional[float] = Query(None, ge=0.0, le=1000.0, description="Depth in metres"),
) -> Dict[str, Any]:
    """Predict temperature at a single location, date, and depth."""
    engine = get_engine()
    depths_to_query = [depth] if depth is not None else SIH_DEPTHS

    try:
        result = engine.predict_profile(lat=lat, lon=lon, date=date, depths=depths_to_query)
        return result
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Profile endpoint ───────────────────────────────────────────────────────────

@app.get("/api/profile", tags=["Inference"])
def get_profile_query(
    lat: float = Query(..., ge=5.0, le=30.0),
    lon: float = Query(..., ge=45.0, le=105.0),
    date: str = Query(...),
) -> Dict[str, Any]:
    """GET convenience wrapper for a full SIH-depth profile."""
    engine = get_engine()
    try:
        return engine.predict_profile(lat=lat, lon=lon, date=date, depths=SIH_DEPTHS)
    except Exception as e:
        logger.error(f"Profile GET failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/profile", tags=["Inference"])
def get_profile(req: ProfileRequest) -> Dict[str, Any]:
    """Return full temperature profile at a location with uncertainty.

    Supports missing-data masks to test resilience.
    """
    engine = get_engine()

    try:
        result = engine.predict_profile(
            lat=req.lat,
            lon=req.lon,
            date=req.date,
            depths=SIH_DEPTHS,
            masks=req.masks,
        )
        return result
    except Exception as e:
        logger.error(f"Profile prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Metrics endpoint ---------------------------------------------------------

@app.get("/api/metrics", tags=["Evaluation"])
def get_metrics() -> Dict[str, Any]:
    """Return model evaluation metrics."""
    metrics_files = [
        ROOT_DIR / "artifacts" / "metrics" / "ocean_embed_evaluation_report.json",
        ROOT_DIR / "artifacts" / "metrics" / "baseline_metrics.json",
    ]
    for path in metrics_files:
        if path.exists():
            import json
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

    return {
        "status": "RESULT NOT YET AVAILABLE",
        "note": (
            "Model has not been trained on real data yet. "
            "See ROADMAP.md for blockers."
        ),
        "blockers": [
            "CMEMS credentials required for GLORYS12V1 training data",
            "GPU recommended for practical training",
        ],
    }


# --- ARGO comparison endpoint -------------------------------------------------

@app.get("/api/argo-comparison", tags=["Evaluation"])
def get_argo_comparison(
    lat: Optional[float] = Query(None, ge=5.0, le=30.0),
    lon: Optional[float] = Query(None, ge=45.0, le=105.0),
    date: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Return comparison between model prediction and nearest ARGO profile."""
    argo_path = ROOT_DIR / "artifacts" / "metrics" / "argo_validation_report.json"
    if argo_path.exists():
        import json
        with open(argo_path, "r", encoding="utf-8") as f:
            return json.load(f)

    return {
        "status": "RESULT NOT YET AVAILABLE",
        "note": (
            "ARGO validation requires: (1) downloaded ARGO profiles, "
            "(2) trained OceanEmbed model. See ARGO_VALIDATION.md."
        ),
        "lat": lat,
        "lon": lon,
        "date": date,
    }


# --- Ablations endpoint --------------------------------------------------------

@app.get("/api/ablations", tags=["Evaluation"])
def get_ablations() -> Dict[str, Any]:
    """Return ablation study benchmarks for OceanEmbed vs 5 baselines."""
    ablation_path = ROOT_DIR / "artifacts" / "metrics" / "ablation_study_report.json"
    if ablation_path.exists():
        import json
        with open(ablation_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    from src.evaluation.ablations import generate_ablation_benchmarks
    return generate_ablation_benchmarks()


# --- Transect endpoint (2D Depth-Longitude Basin Slice) ------------------------

@app.get("/api/map", tags=["Inference"])
def get_map(
    date: str = Query(..., description="Date YYYY-MM-DD"),
    depth: float = Query(0.0, ge=0.0, le=1000.0),
    lat_step: float = Query(1.0, ge=0.5, le=5.0),
    lon_step: float = Query(1.0, ge=0.5, le=5.0),
) -> Dict[str, Any]:
    """Coarse North Indian Ocean temperature field at one depth."""
    engine = get_engine()
    try:
        return engine.predict_map(date=date, depth=depth, lat_step=lat_step, lon_step=lon_step)
    except Exception as e:
        logger.error(f"Map prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transect", tags=["Inference"])
def get_transect(
    lat: float = Query(15.0, ge=5.0, le=30.0, description="Latitude for cross-section (5-30°N)"),
    date: str = Query("2020-07-15", description="Date in YYYY-MM-DD format"),
) -> Dict[str, Any]:
    """Return 2D cross-section across Indian Ocean basin (45°E to 105°E)."""
    engine = get_engine()
    try:
        return engine.predict_transect(lat=lat, date=date)
    except Exception as e:
        logger.error(f"Transect failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Main entrypoint for direct python execution ------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True, app_dir=str(ROOT_DIR))

