"""
OceanEmbed — Tests for Inference Engine and Resilience.
"""

from pathlib import Path
try:
    import pytest
except ImportError:
    pytest = None

from src.data.grid import SIH_DEPTHS
from src.inference.engine import OceanEmbedEngine


def test_inference_engine_continuous_query():
    engine = OceanEmbedEngine()
    # Query non-standard depth e.g. 137.5m
    res = engine.predict_profile(
        lat=15.0,
        lon=70.0,
        date="2020-06-15",
        depths=[137.5],
    )
    assert res["lat"] == 15.0
    assert res["lon"] == 70.0
    assert res["depths"] == [137.5]
    assert len(res["temperatures"]) == 1
    assert len(res["uncertainties"]) == 1
    assert 2.0 <= res["temperatures"][0] <= 32.0
    assert res["uncertainties"][0] > 0.0


def test_missing_modality_uncertainty_dilation():
    engine = OceanEmbedEngine()
    # 1. Full observations
    res_full = engine.predict_profile(
        lat=15.0,
        lon=70.0,
        date="2020-06-15",
        depths=SIH_DEPTHS,
    )
    u_full = sum(res_full["uncertainties"]) / len(res_full["uncertainties"])

    # 2. Missing SSS and SSH
    res_missing = engine.predict_profile(
        lat=15.0,
        lon=70.0,
        date="2020-06-15",
        depths=SIH_DEPTHS,
        masks={"sss": True, "ssh": True},
    )
    u_missing = sum(res_missing["uncertainties"]) / len(res_missing["uncertainties"])

    # Uncertainty MUST increase when modalities are missing
    assert u_missing > u_full, f"Expected {u_missing} > {u_full}"
