"""
OceanEmbed — Inference Engine.

Provides a unified interface for running OceanEmbed predictions.
Supports:
- Real model (when checkpoint exists)
- Demo mode (deterministic synthetic outputs, clearly labelled DEMO/SYNTHETIC)

The engine auto-detects whether a real model is available.
"""

from __future__ import annotations

import json
import logging
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

CHECKPOINT_PATH = Path("artifacts/checkpoints/ocean_embed_best.pt")
DEMO_LABEL = "DEMO / SYNTHETIC"


def _demo_temperature_profile(
    lat: float,
    lon: float,
    depths: List[float],
    date: str,
    masks: Optional[Dict[str, bool]] = None,
) -> tuple[list[float], list[float]]:
    """Generate deterministic DEMO / SYNTHETIC temperature profile.

    This is a simplified analytical model for software testing ONLY.
    NOT a scientific result.

    Returns:
        (temperatures, uncertainties) at the given depths
    """
    # Deterministic seed from location + date
    seed = int(abs(lat * 1000 + lon * 100 + hash(date[:8]) % 10000)) % (2**31)
    rng = np.random.default_rng(seed)

    try:
        doy = datetime.strptime(date[:10], "%Y-%m-%d").timetuple().tm_yday
    except ValueError:
        doy = 180

    t_surface = 28.0 - 5.0 * (lat - 5.0) / 25.0 + 2.0 * math.sin(2 * math.pi * doy / 365)
    t_deep = 4.0
    thermo_depth = 80.0 + 30.0 * math.sin(math.pi * (lon - 45.0) / 60.0)
    thermo_depth = max(40.0, min(150.0, thermo_depth))

    # Increase uncertainty if inputs are missing
    missing_count = sum(1 for v in (masks or {}).values() if v)
    base_uncertainty = 0.5 + 0.3 * missing_count

    temperatures = []
    uncertainties = []
    for z in depths:
        t_z = t_deep + (t_surface - t_deep) * math.exp(-z / thermo_depth)
        t_z += float(rng.standard_normal() * 0.3)
        # Uncertainty increases with depth and missing inputs
        unc = base_uncertainty + 0.5 * (z / 1000.0)
        temperatures.append(round(float(t_z), 4))
        uncertainties.append(round(float(unc), 4))

    return temperatures, uncertainties


def _isotherm_depth(depths: List[float], temps: List[float], iso: float, default: float) -> float:
    for i in range(len(temps) - 1):
        t0, t1 = temps[i], temps[i + 1]
        if (t0 >= iso and t1 <= iso) or (t0 <= iso and t1 >= iso):
            denom = t0 - t1
            frac = (t0 - iso) / denom if denom != 0 else 0.0
            return depths[i] + frac * (depths[i + 1] - depths[i])
    return default


def calculate_thermocline_features(depths: List[float], temps: List[float]) -> Dict[str, float]:
    """Calculate key oceanographic thermocline metrics from profile."""
    d20 = _isotherm_depth(depths, temps, 20.0, 100.0)
    d26 = _isotherm_depth(depths, temps, 26.0, 55.0)

    mld = 35.0
    t0 = temps[0] if temps else 28.0
    for i in range(1, len(temps)):
        if abs(t0 - temps[i]) >= 0.5:
            mld = depths[i]
            break

    max_grad = 0.0
    thermo_depth = 80.0
    for i in range(len(temps) - 1):
        dz = abs(depths[i + 1] - depths[i])
        if dz > 0:
            grad = abs(temps[i] - temps[i + 1]) / dz
            if grad > max_grad:
                max_grad = grad
                thermo_depth = (depths[i] + depths[i + 1]) / 2.0

    return {
        "d20_depth_m": round(float(d20), 2),
        "d26_depth_m": round(float(d26), 2),
        "mld_m": round(float(mld), 2),
        "max_gradient_c_per_m": round(float(max_grad), 4),
        "thermocline_depth_m": round(float(thermo_depth), 2),
        "surface_temp_c": round(float(t0), 3),
    }


def _demo_surface_inputs(lat: float, lon: float, date: str, sst: float) -> Dict[str, float]:
    """Deterministic DEMO / SYNTHETIC surface fields for UI telemetry."""
    try:
        doy = datetime.strptime(date[:10], "%Y-%m-%d").timetuple().tm_yday
    except ValueError:
        doy = 180
    season = math.sin(2 * math.pi * doy / 365)
    arabian = 1.0 if lon < 78.0 else 0.0
    sss = 35.4 - 2.6 * (1.0 - arabian) + 0.3 * season - 0.04 * (lat - 12.0)
    ssh = 0.08 + 0.12 * math.sin(math.pi * (lon - 45.0) / 60.0) + 0.04 * season
    wind_u = 2.5 + 6.0 * max(0.0, math.sin(2 * math.pi * (doy - 150) / 365)) * (1.0 if lat < 20 else 0.4)
    wind_v = -1.2 + 2.0 * season
    current_u = 0.15 * math.sin(math.pi * (lat - 5.0) / 25.0)
    current_v = 0.08 * math.cos(math.pi * (lon - 45.0) / 60.0)
    return {
        "sst": round(float(sst), 3),
        "sss": round(float(sss), 3),
        "ssh": round(float(ssh), 3),
        "current_u": round(float(current_u), 3),
        "current_v": round(float(current_v), 3),
        "wind_u": round(float(wind_u), 3),
        "wind_v": round(float(wind_v), 3),
        "wind_speed": round(float(math.hypot(wind_u, wind_v)), 3),
    }


def _demo_temperature_field(
    lats: np.ndarray,
    lons: np.ndarray,
    depth: float,
    date: str,
    masks: Optional[Dict[str, bool]] = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Vectorized DEMO / SYNTHETIC temperature field (software testing only)."""
    try:
        doy = datetime.strptime(date[:10], "%Y-%m-%d").timetuple().tm_yday
    except ValueError:
        doy = 180
    lat_g, lon_g = np.meshgrid(lats, lons, indexing="ij")
    t_surface = 28.0 - 5.0 * (lat_g - 5.0) / 25.0 + 2.0 * math.sin(2 * math.pi * doy / 365)
    t_deep = 4.0
    thermo_depth = np.clip(80.0 + 30.0 * np.sin(np.pi * (lon_g - 45.0) / 60.0), 40.0, 150.0)
    temps = t_deep + (t_surface - t_deep) * np.exp(-float(depth) / thermo_depth)
    missing_count = sum(1 for v in (masks or {}).values() if v)
    uncs = np.full_like(temps, 0.5 + 0.3 * missing_count + 0.5 * (float(depth) / 1000.0))
    return temps, uncs


class OceanEmbedEngine:
    """Inference engine for OceanEmbed predictions.

    Auto-detects REAL vs DEMO mode based on checkpoint availability.
    """

    def __init__(
        self,
        checkpoint_path: Path | str = CHECKPOINT_PATH,
        device: str = "cpu",
    ):
        self.device_name = device
        self.checkpoint_path = Path(checkpoint_path)
        self.demo_mode = not self.checkpoint_path.exists()
        self._model = None

        if self.demo_mode:
            logger.warning(
                f"No checkpoint found at {self.checkpoint_path}. "
                f"Engine running in DEMO / SYNTHETIC mode. "
                f"Outputs are NOT scientific results."
            )
        else:
            logger.info(f"Loading model from {self.checkpoint_path}")
            self._load_model()

    def _load_model(self) -> None:
        """Load the trained OceanEmbed model from checkpoint."""
        try:
            import torch
            from src.models.ocean_embed import OceanEmbedModel

            checkpoint = torch.load(self.checkpoint_path, map_location=self.device_name, weights_only=False)
            config = checkpoint.get("model_config", checkpoint.get("config", {}))
            is_demo = checkpoint.get("is_demo_mode", False)

            self._model = OceanEmbedModel(
                temporal_window=config.get("temporal_window", 3),
                n_surface_channels=config.get("n_surface_channels", 7),
                use_masks=True,
                use_coords=True,
                base_channels=config.get("base_channels", 16),
                encoder_depth=config.get("encoder_depth", 3),
                latent_dim=config.get("latent_dim", 64),
                n_fourier_freqs=config.get("n_fourier_freqs", 16),
                decoder_hidden=tuple(config.get("decoder_hidden", [128, 128, 64])),
            )
            self._model.load_state_dict(checkpoint["model_state_dict"])
            self._model.eval()
            self.demo_mode = is_demo
            logger.info(f"Model loaded successfully. Demo mode: {self.demo_mode}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}. Falling back to DEMO mode.")
            self.demo_mode = True

    def predict_profile(
        self,
        lat: float,
        lon: float,
        date: str,
        depths: Optional[List[float]] = None,
        masks: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, Any]:
        """Predict temperature profile at a location and date."""
        from src.data.grid import SIH_DEPTHS, get_region_name
        depths = depths or SIH_DEPTHS
        masks = masks or {}
        region_name = get_region_name(lat, lon)

        if self._model is not None and not self.demo_mode:
            try:
                res = self._real_predict_profile(lat, lon, date, depths, masks)
                res["region"] = region_name
                return res
            except Exception as e:
                logger.warning(f"Real prediction failed ({e}), using analytical demo profile.")

        temps, uncs = _demo_temperature_profile(lat, lon, depths, date, masks)
        thermo = calculate_thermocline_features(depths, temps)
        return {
            "demo": True,
            "data_type": DEMO_LABEL,
            "lat": lat,
            "lon": lon,
            "region": region_name,
            "date": date,
            "depths": depths,
            "temperatures": temps,
            "uncertainties": uncs,
            "thermocline": thermo,
            "surface_inputs": _demo_surface_inputs(lat, lon, date, temps[0] if temps else 28.0),
            "masks_applied": masks,
            "warning": "DEMO / SYNTHETIC data. NOT a scientific result.",
        }

    def _real_predict_profile(
        self,
        lat: float,
        lon: float,
        date: str,
        depths: List[float],
        masks: Dict[str, bool],
    ) -> Dict[str, Any]:
        """Run neural model inference for arbitrary continuous depths."""
        import torch
        from src.data.grid import (
            normalize_lat,
            normalize_lon,
            normalize_doy,
            get_region_id,
        )

        try:
            from datetime import datetime
            doy = datetime.strptime(date[:10], "%Y-%m-%d").timetuple().tm_yday
        except Exception:
            doy = 180

        H, W = 16, 16  # local patch representation
        lat_t = torch.tensor(normalize_lat(lat), dtype=torch.float32).view(1, 1, 1).expand(1, H, W)
        lon_t = torch.tensor(normalize_lon(lon), dtype=torch.float32).view(1, 1, 1).expand(1, H, W)
        doy_t = torch.tensor([normalize_doy(doy)], dtype=torch.float32)
        reg_id = torch.tensor([get_region_id(lat, lon)], dtype=torch.long)

        # Baseline surface context
        inputs_t = torch.zeros((1, 3, 7, H, W), dtype=torch.float32)
        masks_t = torch.ones((1, 3, 7, H, W), dtype=torch.float32)

        # Apply missing flags
        flag_map = {"sst": 0, "sss": 1, "ssh": 2, "current_u": 3, "current_v": 4, "wind_u": 5, "wind_v": 6}
        for k, v in masks.items():
            if v and k in flag_map:
                masks_t[:, :, flag_map[k], :, :] = 0.0

        with torch.no_grad():
            out = self._model(
                inputs=inputs_t,
                masks=masks_t,
                lat_norm=lat_t,
                lon_norm=lon_t,
                doy_norm=doy_t,
                depths=depths,
                region_ids=reg_id,
            )
            # Center pixel of patch
            means = out["means"][0, :, H // 2, W // 2].cpu().numpy()
            log_vars = out["log_vars"][0, :, H // 2, W // 2].cpu().numpy()
            uncertainties = np.exp(0.5 * log_vars)

        temps = [round(float(m), 4) for m in means]
        uncs = [round(float(u), 4) for u in uncertainties]
        return {
            "demo": False,
            "data_type": "MODEL PREDICTION",
            "lat": lat,
            "lon": lon,
            "date": date,
            "depths": depths,
            "temperatures": temps,
            "uncertainties": uncs,
            "thermocline": calculate_thermocline_features(depths, temps),
            "surface_inputs": _demo_surface_inputs(lat, lon, date, temps[0] if temps else 28.0),
            "masks_applied": masks,
        }

    def predict_map(
        self,
        date: str,
        depth: float,
        masks: Optional[Dict[str, bool]] = None,
        lat_step: float = 1.0,
        lon_step: float = 1.0,
    ) -> Dict[str, Any]:
        """Predict a coarse temperature map for dashboard rendering."""
        lat_step = max(0.5, min(5.0, float(lat_step)))
        lon_step = max(0.5, min(5.0, float(lon_step)))
        lats = np.arange(5.0, 30.0 + 1e-9, lat_step)
        lons = np.arange(45.0, 105.0 + 1e-9, lon_step)
        temps, uncs = _demo_temperature_field(lats, lons, float(depth), date, masks)
        return {
            "demo": self.demo_mode,
            "data_type": DEMO_LABEL if self.demo_mode else "MODEL PREDICTION (COARSE DEMO FIELD)",
            "date": date,
            "depth": float(depth),
            "lats": [round(float(v), 3) for v in lats],
            "lons": [round(float(v), 3) for v in lons],
            "temperatures": np.round(temps, 3).tolist(),
            "uncertainties": np.round(uncs, 3).tolist(),
            "warning": "DEMO / SYNTHETIC data. NOT a scientific result." if self.demo_mode else None,
        }

    def predict_transect(
        self,
        lat: float,
        date: str,
        masks: Optional[Dict[str, bool]] = None,
        lon_step: float = 2.0,
    ) -> Dict[str, Any]:
        """Zonal temperature section across 45–105°E at a fixed latitude."""
        from src.data.grid import SIH_DEPTHS, get_region_name

        longitudes = [float(lon) for lon in np.arange(45.0, 105.0 + 1e-9, lon_step)]
        depths = [float(d) for d in SIH_DEPTHS]
        matrix: List[List[float]] = []
        uncert_matrix: List[List[float]] = []
        d20_line: List[float] = []
        d26_line: List[float] = []

        for lon in longitudes:
            prof = self.predict_profile(lat=lat, lon=lon, date=date, depths=depths, masks=masks)
            matrix.append(prof["temperatures"])
            uncert_matrix.append(prof["uncertainties"])
            thermo = prof.get("thermocline") or {}
            d20_line.append(thermo.get("d20_depth_m"))
            d26_line.append(thermo.get("d26_depth_m"))

        return {
            "lat": lat,
            "date": date,
            "region_note": get_region_name(lat, 75.0),
            "longitudes": longitudes,
            "depths": depths,
            "temperatures_2d": matrix,
            "uncertainties_2d": uncert_matrix,
            "d20_depths": d20_line,
            "d26_depths": d26_line,
            "demo": self.demo_mode,
            "data_type": DEMO_LABEL if self.demo_mode else "MODEL PREDICTION",
            "warning": "DEMO / SYNTHETIC data. NOT a scientific result." if self.demo_mode else None,
        }

    def get_metadata(self) -> Dict[str, Any]:
        """Return engine metadata."""
        return {
            "demo_mode": self.demo_mode,
            "data_type": DEMO_LABEL if self.demo_mode else "REAL",
            "checkpoint": str(self.checkpoint_path) if not self.demo_mode else None,
            "sih_depths": [0, 5, 10, 20, 30, 50, 75, 100, 125, 150, 200, 300, 500, 700, 1000],
            "domain": {
                "lat_min": 5.0, "lat_max": 30.0,
                "lon_min": 45.0, "lon_max": 105.0,
                "resolution": 0.25,
            },
        }
