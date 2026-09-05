# OceanEmbed — Model Description

## Version History

### V1 — Baseline (CNN Encoder-Decoder)

A U-Net-style CNN that maps 7 surface channels to 15 fixed-depth temperature maps.

**Input**: (B, 7, H, W) — SST, SSS, SSH, current_U, current_V, wind_U, wind_V  
**Output**: (B, 15, H, W) — temperature at 15 SIH standard depths  
**Loss**: MSE  
**Parameters**: ~1M (base_channels=32, depth=4)

### V2 — Temporal Context

Extends V1 with a 3-day observation window (t-2, t-1, t).

**Input**: (B, 3×7, H, W)  
**Temporal fusion**: Channel concatenation before encoder

### V3 — Missing-Data Masks

Adds binary validity masks for all 7 channels.

**Input**: (B, 3×14, H, W) — 7 channels + 7 masks per timestep  
**Mask handling**: Channels are zero-filled where mask=0

### V4 — Uncertainty

Adds heteroscedastic uncertainty estimation.

**Output**: (B, 15, H, W) mean + (B, 15, H, W) log_variance  
**Loss**: Gaussian NLL = 0.5 * (log_var + (T - μ)² * exp(-log_var))

### V5 — Continuous Depth

Replaces fixed 15-depth output head with a continuous depth decoder.

**Input**: Surface encoder output + depth query γ(z)  
**Output**: Temperature mean + variance at any depth z ∈ [0, 1000] m  
**Depth encoding**: Fourier features with L=16 frequencies

### V6 — Regional Conditioning

Adds a learned region embedding.

**Input**: + region_id (0=Arabian Sea, 1=Bay of Bengal, 2=Open Ocean)  
**Implementation**: Learned embedding (16-dim) added to bottleneck

### V7 — Physics / Thermocline

Adds configurable thermocline regularization.

**Physics loss**: L1(thermocline_depth_predicted, thermocline_depth_glorys)  
**Weight**: 0.01 (ablated; see training_config.yaml)

## Final OceanEmbed

All V1–V7 components combined. Parameters ~5–10M depending on config.

## File Locations

| Component | File |
|---|---|
| Grid utilities | `src/data/grid.py` |
| Dataset classes | `src/data/dataset.py` |
| Normalization | `src/data/normalization.py` |
| Baseline model | `src/models/baseline.py` |
| OceanEmbed model | `src/models/ocean_embed.py` |
| Depth encoder | `src/models/depth_encoder.py` |
| Uncertainty head | `src/models/uncertainty_head.py` |
| Losses | `src/training/losses.py` |
| Metrics | `src/evaluation/metrics.py` |
| Inference engine | `src/inference/engine.py` |
