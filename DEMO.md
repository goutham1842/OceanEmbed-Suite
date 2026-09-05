# OceanEmbed — Demo Mode

## Purpose

Demo mode exists for software and UI testing when real model outputs are
not yet available (e.g., before training data is downloaded, or before
model training is complete).

**DEMO / SYNTHETIC data is NEVER used as scientific evidence.**

## Activation

Demo mode is controlled by:

```env
OCEANEMBED_DEMO_MODE=true
```

The backend automatically switches to REAL mode when a trained model
checkpoint is found at `artifacts/checkpoints/ocean_embed_best.pt`.

## Behaviour in Demo Mode

1. The API returns physically plausible but **deterministically synthetic**
   temperature profiles.
2. Every API response includes `"demo": true` and `"data_type": "SYNTHETIC"`.
3. The frontend displays a prominent **`⚠️ DEMO / SYNTHETIC DATA`** banner.
4. Synthetic values are generated from a simple analytical model:
   - SST-like surface temperature
   - Exponential thermocline decay with noise
   - Depth-dependent cooling
5. The same synthetic profile is always returned for the same input
   (deterministic for reproducibility).

## Synthetic Temperature Model (Demo Only)

The demo uses:

```
T_surface = 28 - 5*(lat - 5)/25 + 2*sin(2π*doy/365)
T(z) = T_deep + (T_surface - T_deep) * exp(-z / thermocline_depth)
thermocline_depth = 50 + 30*sin(π*lon/60)
T_deep = 4.0 °C
```

This is an **illustrative approximation only**, not a scientific model.

## Identifying Demo vs Real Mode

| Indicator | Demo Mode | Real Mode |
|---|---|---|
| Frontend banner | ⚠️ DEMO / SYNTHETIC DATA | Real model active |
| API field `demo` | `true` | `false` |
| API field `data_type` | `"SYNTHETIC"` | `"REAL"` |
| Checkpoint present | No | Yes |
| Metrics displayed | Not displayed | Actual measured metrics |

## When Demo Mode Ends

Once the following are available:
1. Real training data downloaded and preprocessed
2. Baseline model trained and evaluated
3. Checkpoint saved to `artifacts/checkpoints/`

Demo mode is automatically disabled and real model outputs are served.
