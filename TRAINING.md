# OceanEmbed — Training

## Environment

- **Framework**: PyTorch 2.8.0+cpu
- **Device**: CPU (no GPU; see LIMITATIONS.md)
- **Config**: `configs/training_config.yaml`

## Training Command

```bash
# Baseline (V1)
python scripts/train/train_baseline.py \
    --config configs/training_config.yaml \
    --model-config configs/model_config.yaml

# OceanEmbed Full
python scripts/train/train_ocean_embed.py \
    --config configs/training_config.yaml \
    --model-config configs/model_config.yaml

# Resume from checkpoint
python scripts/train/train_ocean_embed.py \
    --resume artifacts/checkpoints/ocean_embed_last.pt
```

## Chronological Splits

- **Train**: 1993-01-01 to 2018-12-31
- **Validation**: 2019-01-01 to 2020-12-31
- **Test**: 2021-01-01 to 2022-12-31

Normalization statistics computed from training data only.

## Hyperparameters (CPU-friendly defaults)

| Hyperparameter | Value | Notes |
|---|---|---|
| Batch size | 4 | Reduced for CPU |
| Learning rate | 1e-3 | AdamW |
| Optimizer | AdamW | weight_decay=1e-4 |
| Scheduler | CosineAnnealingLR | T_max=50 |
| Max epochs | 50 | Subject to early stopping |
| Early stopping patience | 10 | Monitor: val_rmse |
| Seed | 42 | Reproducible |

## Ablation Experiments

See `configs/training_config.yaml` for the full ablation sequence:

1. Baseline
2. Baseline + temporal context
3. Baseline + missing masks
4. Baseline + uncertainty
5. Baseline + continuous depth
6. Baseline + regional conditioning
7. Baseline + physics/thermocline
8. OceanEmbed full (all components)

## Checkpoints

Checkpoints saved to `artifacts/checkpoints/`.
Best (lowest val_rmse) saved as `ocean_embed_best.pt`.
Last saved as `ocean_embed_last.pt`.

## Status

**RESULT NOT YET AVAILABLE** — blocked on real training data (CMEMS credentials needed).
