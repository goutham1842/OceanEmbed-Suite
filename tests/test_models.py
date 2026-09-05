"""
OceanEmbed — Tests for Baseline and OceanEmbed Deep Learning Models.
"""

import torch
import pytest

from src.models.baseline import BaselineModel
from src.models.depth_encoder import FourierDepthEncoder
from src.models.ocean_embed import OceanEmbedModel


def test_baseline_model_forward():
    model = BaselineModel(
        in_channels=7,
        out_depths=15,
        base_channels=8,
        encoder_depth=2,
    )
    x = torch.randn(2, 7, 32, 32)
    out = model(x)
    assert out.shape == (2, 15, 32, 32)
    assert torch.all(torch.isfinite(out))


def test_fourier_depth_encoder():
    encoder = FourierDepthEncoder(n_frequencies=16, max_depth=1000.0)
    assert encoder.out_dim == 33  # 1 (norm_z) + 2 * 16

    # Test single depth and batch of arbitrary depths
    depths = torch.tensor([0.0, 137.5, 173.5, 421.0, 1000.0])
    emb = encoder(depths)
    assert emb.shape == (5, 33)
    assert torch.all(torch.isfinite(emb))


def test_ocean_embed_continuous_query():
    model = OceanEmbedModel(
        temporal_window=3,
        n_surface_channels=7,
        use_masks=True,
        use_coords=True,
        base_channels=8,
        encoder_depth=2,
        latent_dim=32,
        n_fourier_freqs=8,
        decoder_hidden=(32, 16),
    )

    B, H, W = 2, 16, 16
    inputs = torch.randn(B, 3, 7, H, W)
    masks = torch.ones(B, 3, 7, H, W)
    lat_norm = torch.zeros(B, H, W)
    lon_norm = torch.zeros(B, H, W)
    doy_norm = torch.zeros(B)
    region_ids = torch.zeros(B, dtype=torch.long)

    # 1. Query single arbitrary depth (e.g. 137.5 m)
    single_out = model(
        inputs=inputs,
        masks=masks,
        lat_norm=lat_norm,
        lon_norm=lon_norm,
        doy_norm=doy_norm,
        depths=[137.5],
        region_ids=region_ids,
    )
    assert single_out["means"].shape == (B, 1, H, W)
    assert single_out["log_vars"].shape == (B, 1, H, W)
    assert torch.all(torch.isfinite(single_out["means"]))
    assert torch.all(torch.isfinite(single_out["log_vars"]))

    # 2. Query multiple arbitrary continuous depths
    arbitrary_depths = [12.3, 137.5, 289.0, 712.5]
    out = model(
        inputs=inputs,
        masks=masks,
        lat_norm=lat_norm,
        lon_norm=lon_norm,
        doy_norm=doy_norm,
        depths=arbitrary_depths,
        region_ids=region_ids,
    )
    assert out["means"].shape == (B, 4, H, W)
    assert out["log_vars"].shape == (B, 4, H, W)
