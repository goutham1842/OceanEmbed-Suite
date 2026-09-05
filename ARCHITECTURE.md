# OceanEmbed — Architecture

## Overview

OceanEmbed implements a continuous-depth-conditioned ocean reconstruction model.
The system maps multimodal daily surface satellite observations to subsurface
temperature at arbitrary depths from 0 to 1000 m.

## Conceptual Design

```
Surface observations (SST, SSS, SSH, current U/V, wind U/V)
    + Missingness masks (7 binary masks)
    + Coordinate encoding (lat, lon, normalized)
    + Temporal context (t-2, t-1, t)
              ↓
    ┌─────────────────────────────┐
    │  Multimodal Surface Encoder │  ← U-Net style, 4-level
    │  (CNN backbone)             │
    └────────────┬────────────────┘
                 ↓
    ┌─────────────────────────────┐
    │  Spatial-Temporal Features  │
    │  (+ regional conditioning)  │
    └────────────┬────────────────┘
                 ↓
    ┌─────────────────────────────┐
    │  Ocean Latent Embedding     │  ← 128-dim per grid point
    └────────────┬────────────────┘
                 ↓  + depth query z
    ┌─────────────────────────────┐
    │  Continuous Depth Decoder   │  ← Fourier depth encoding
    │  (MLP conditioned on E, z)  │
    └────────────┬────────────────┘
                 ↓
    ┌─────────────────────────────┐
    │  Temperature (μ) + σ²       │  ← heteroscedastic output
    └─────────────────────────────┘
```

## Mathematical Formulation

```
E(x,y,t) = Encoder(X_{t-2:t}, mask_{t-2:t}, lat, lon, region)

T(x,y,z,t) = Decoder(E(x,y,t), γ(z), lat, lon, t)

U(x,y,z,t) = UncertaintyHead(E(x,y,t), γ(z), mask)
```

Where:
- `X_{t-2:t}` = 3-day surface observation window
- `mask` = binary validity masks per channel
- `γ(z)` = Fourier positional encoding of normalized depth
- `T` = predicted temperature mean
- `U` = predicted temperature variance (log-variance parameterization)

## Model Versions (Development Sequence)

| Version | Components | Status |
|---|---|---|
| V1 Baseline | 7-channel CNN encoder-decoder, 15 fixed depths | Implemented |
| V2 + Temporal | 3-day window | Implemented |
| V3 + Masks | Explicit missing-observation masks | Implemented |
| V4 + Uncertainty | Heteroscedastic regression | Implemented |
| V5 + Continuous Depth | Fourier-encoded depth query | Implemented |
| V6 + Regional | Bay of Bengal / Arabian Sea conditioning | Implemented |
| V7 + Physics | Thermocline regularization (configurable) | Implemented |
| OceanEmbed Full | All components combined | Implemented |

## Encoder Architecture (U-Net Style)

- **Input**: (B, T×C_in, H, W) where T=3 timesteps, C_in=7 channels + 7 masks + 2 coords
- **Encoder levels**: 4 downsampling blocks with residual connections
- **Channel progression**: 32 → 64 → 128 → 256
- **Bottleneck**: 256 channels with optional spatial attention
- **Decoder**: 4 upsampling blocks with skip connections
- **Output**: Ocean latent embedding (B, 128, H, W)

## Depth Encoding (Fourier / Positional)

For depth query `z ∈ [0, 1000]`:

```
z_norm = z / 1000.0  ∈ [0, 1]

γ(z) = [sin(2πk·z_norm), cos(2πk·z_norm)]  for k = 1..L

concat(z_norm, γ(z))  →  (2L+1) dimensional depth embedding
```

Fourier frequencies `L=16` used, giving 33-dim depth embedding.

## Depth Decoder (MLP)

For each grid point:

```
Input: concat(E_flat, γ(z), lat, lon, day_of_year)
Layers: Linear(N_in, 256) → GELU → Linear(256, 256) → GELU → Linear(256, 128) → GELU
Output head (mean): Linear(128, 1)
Output head (log_var): Linear(128, 1)
```

## Uncertainty Estimation

Heteroscedastic regression:
- Model outputs `μ(z)` and `log σ²(z)` per depth
- Loss: Gaussian NLL = `0.5 * (log σ² + (T - μ)² / σ²)`
- Uncertainty represents **predictive variance** — reflects both
  model uncertainty and input data quality
- **NOT** calibrated confidence unless explicitly evaluated against held-out data

## Regional Conditioning

- Regions: Arabian Sea, Bay of Bengal, Open Ocean
- Region determined from grid point location at runtime
- Implementation: learned region embedding (16-dim) concatenated to
  bottleneck features
- Shared backbone ensures transfer learning across regions

## Thermocline Analysis

- Vertical gradient: `dT/dz` computed from continuous depth decoder output
- Thermocline depth: depth of maximum `|dT/dz|` above 300 m
- Compared against GLORYS12V1 reference thermocline
- Physics loss: optional L1 penalty on thermocline depth discrepancy
  (weight configurable; see `configs/training_config.yaml`)

## Input Channels Summary

| Channel | Source | Units | Mask |
|---|---|---|---|
| SST | OSTIA | °C | SST_mask |
| SSS | CMEMS Multi-Obs | PSU | SSS_mask |
| SSH/SLA | DUACS | m | SSH_mask |
| current_U | DUACS geostrophic | m/s | CU_mask |
| current_V | DUACS geostrophic | m/s | CV_mask |
| wind_U | ERA5 | m/s | WU_mask |
| wind_V | ERA5 | m/s | WV_mask |
| lat_coord | Grid | normalized | — |
| lon_coord | Grid | normalized | — |
