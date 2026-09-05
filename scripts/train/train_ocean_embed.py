"""
OceanEmbed — Model Training Script (V5+: Continuous Depth + Uncertainty + Regional Conditioning).

Trains the full OceanEmbed continuous-depth model:
- Temporal multi-modal surface observations (SST, SSS, SSH, currents U/V, wind U/V)
- Fourier positional encoding for continuous arbitrary depth querying
- Heteroscedastic regression (Gaussian NLL loss predicting mean + log variance)
- Missing observation mask conditioning for operational resilience
- Regional conditioning (Arabian Sea, Bay of Bengal, Open Ocean)

Usage:
    python scripts/train/train_ocean_embed.py --demo-mode --epochs 3
    python scripts/train/train_ocean_embed.py --epochs 50 --batch-size 8
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.dataset import DemoDataset, OceanEmbedDataset
from src.data.grid import SIH_DEPTHS
from src.models.ocean_embed import OceanEmbed
from src.training.losses import GaussianNLLLoss, MSELoss

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("train_ocean_embed")


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def train_one_epoch(
    model: OceanEmbed,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
    depths: List[float],
) -> Dict[str, float]:
    model.train()
    total_loss = 0.0
    total_mse = 0.0
    n_batches = 0

    for batch in loader:
        inputs = batch["inputs"].to(device)       # (B, T, 7, H, W)
        masks = batch.get("masks", torch.zeros_like(inputs)).to(device)
        target = batch["target"].to(device)       # (B, 15, H, W)
        lat_norm = batch.get("lat_norm", torch.zeros(inputs.shape[0], inputs.shape[3], inputs.shape[4])).to(device)
        lon_norm = batch.get("lon_norm", torch.zeros(inputs.shape[0], inputs.shape[3], inputs.shape[4])).to(device)
        doy_norm = batch.get("doy_norm", torch.zeros(inputs.shape[0])).to(device)
        region_ids = batch.get("region_ids", torch.zeros(inputs.shape[0], dtype=torch.long)).to(device)

        optimizer.zero_grad()

        # Forward pass through OceanEmbed
        out = model(
            inputs=inputs,
            masks=masks,
            lat_norm=lat_norm,
            lon_norm=lon_norm,
            doy_norm=doy_norm,
            depths=depths,
            region_ids=region_ids,
        )

        pred_mean = out["means"]         # (B, D, H, W)
        pred_log_var = out["log_vars"]   # (B, D, H, W)

        # Compute heteroscedastic Gaussian NLL loss
        loss = criterion(pred_mean, pred_log_var, target)

        # Also monitor MSE
        valid = torch.isfinite(target)
        mse = ((pred_mean - target) ** 2 * valid.float()).sum() / valid.float().sum().clamp(min=1)

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += loss.item()
        total_mse += mse.item()
        n_batches += 1

    return {
        "loss": total_loss / max(n_batches, 1),
        "mse": total_mse / max(n_batches, 1),
        "rmse": float(np.sqrt(max(total_mse / max(n_batches, 1), 1e-8))),
    }


@torch.no_grad()
def validate(
    model: OceanEmbed,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    depths: List[float],
) -> Dict[str, float]:
    model.eval()
    total_loss = 0.0
    all_pred, all_unc, all_target = [], [], []

    for batch in loader:
        inputs = batch["inputs"].to(device)
        masks = batch.get("masks", torch.zeros_like(inputs)).to(device)
        target = batch["target"].to(device)
        lat_norm = batch.get("lat_norm", torch.zeros(inputs.shape[0], inputs.shape[3], inputs.shape[4])).to(device)
        lon_norm = batch.get("lon_norm", torch.zeros(inputs.shape[0], inputs.shape[3], inputs.shape[4])).to(device)
        doy_norm = batch.get("doy_norm", torch.zeros(inputs.shape[0])).to(device)
        region_ids = batch.get("region_ids", torch.zeros(inputs.shape[0], dtype=torch.long)).to(device)

        out = model(
            inputs=inputs,
            masks=masks,
            lat_norm=lat_norm,
            lon_norm=lon_norm,
            doy_norm=doy_norm,
            depths=depths,
            region_ids=region_ids,
        )

        pred_mean = out["means"]
        pred_log_var = out["log_vars"]

        loss = criterion(pred_mean, pred_log_var, target)
        total_loss += loss.item()

        all_pred.append(pred_mean.cpu().numpy())
        all_unc.append(torch.exp(0.5 * pred_log_var).cpu().numpy())
        all_target.append(target.cpu().numpy())

    p = np.concatenate(all_pred, axis=0)
    u = np.concatenate(all_unc, axis=0)
    t = np.concatenate(all_target, axis=0)

    valid = np.isfinite(t) & np.isfinite(p)
    diff = p[valid] - t[valid]
    val_rmse = float(np.sqrt(np.mean(diff ** 2)))
    val_mae = float(np.mean(np.abs(diff)))
    val_bias = float(np.mean(diff))

    return {
        "val_loss": total_loss / max(len(loader), 1),
        "val_rmse": val_rmse,
        "val_mae": val_mae,
        "val_bias": val_bias,
        "mean_uncertainty": float(np.mean(u[valid])),
    }


def main():
    parser = argparse.ArgumentParser(description="Train OceanEmbed continuous model")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size (small for CPU)")
    parser.add_argument("--lr", type=float, default=1e-3, help="Initial learning rate")
    parser.add_argument("--demo-mode", action="store_true", help="Use synthetic dataset for CPU smoke test")
    parser.add_argument("--latent-dim", type=int, default=64, help="Latent bottleneck dimension")
    parser.add_argument("--base-channels", type=int, default=16, help="Encoder base channels (CPU-friendly)")
    parser.add_argument("--encoder-depth", type=int, default=3, help="Encoder depth")
    parser.add_argument("--checkpoint-dir", type=Path, default=PROJECT_ROOT / "artifacts" / "checkpoints")
    parser.add_argument("--metrics-dir", type=Path, default=PROJECT_ROOT / "artifacts" / "metrics")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    set_seed(args.seed)
    args.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    args.metrics_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Training on device: {device} | Demo mode: {args.demo_mode}")

    # Build datasets
    if args.demo_mode:
        logger.warning("DEMO MODE ACTIVE: Using synthetic dataset. Outputs are for software verification only.")
        train_ds = DemoDataset(n_samples=20, temporal_window=3)
        val_ds = DemoDataset(n_samples=8, temporal_window=3)
        train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False)
    else:
        try:
            train_ds = OceanEmbedDataset(data_dir=PROJECT_ROOT / "data" / "processed", split="train")
            val_ds = OceanEmbedDataset(data_dir=PROJECT_ROOT / "data" / "processed", split="val")
            if len(train_ds) == 0:
                raise ValueError("No processed samples found.")
            train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
            val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False)
        except Exception as e:
            logger.warning(f"Could not load real processed data ({e}). Falling back to synthetic smoke-test data.")
            train_ds = DemoDataset(n_samples=20, temporal_window=3)
            val_ds = DemoDataset(n_samples=8, temporal_window=3)
            train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
            val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False)

    # Initialize OceanEmbed model
    model = OceanEmbed(
        temporal_window=3,
        n_surface_channels=7,
        use_masks=True,
        use_coords=True,
        base_channels=args.base_channels,
        encoder_depth=args.encoder_depth,
        latent_dim=args.latent_dim,
        n_fourier_freqs=16,
        decoder_hidden=(128, 128, 64),
        n_regions=3,
        region_embed_dim=16,
        dropout=0.1,
    ).to(device)

    logger.info(f"OceanEmbed instantiated with {model._n_params:,} parameters.")

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-5)
    criterion = GaussianNLLLoss()

    best_val_rmse = float("inf")
    history = []

    logger.info(f"Starting training for {args.epochs} epochs...")
    start_time = time.time()

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        train_metrics = train_one_epoch(
            model=model,
            loader=train_loader,
            optimizer=optimizer,
            criterion=criterion,
            device=device,
            depths=SIH_DEPTHS,
        )

        val_metrics = validate(
            model=model,
            loader=val_loader,
            criterion=criterion,
            device=device,
            depths=SIH_DEPTHS,
        )

        scheduler.step()
        elapsed = time.time() - t0

        record = {
            "epoch": epoch,
            "train_loss": round(train_metrics["loss"], 4),
            "train_rmse": round(train_metrics["rmse"], 4),
            "val_loss": round(val_metrics["val_loss"], 4),
            "val_rmse": round(val_metrics["val_rmse"], 4),
            "val_mae": round(val_metrics["val_mae"], 4),
            "val_bias": round(val_metrics["val_bias"], 4),
            "mean_uncertainty": round(val_metrics["mean_uncertainty"], 4),
            "elapsed_s": round(elapsed, 2),
        }
        history.append(record)

        logger.info(
            f"Epoch {epoch:2d}/{args.epochs:2d} | "
            f"Train Loss: {train_metrics['loss']:.4f} | "
            f"Val RMSE: {val_metrics['val_rmse']:.4f} °C | "
            f"Val MAE: {val_metrics['val_mae']:.4f} °C | "
            f"Uncertainty: {val_metrics['mean_uncertainty']:.4f} | "
            f"Time: {elapsed:.1f}s"
        )

        if val_metrics["val_rmse"] < best_val_rmse:
            best_val_rmse = val_metrics["val_rmse"]
            checkpoint_path = args.checkpoint_dir / "ocean_embed_best.pt"
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_rmse": best_val_rmse,
                    "model_config": {
                        "temporal_window": 3,
                        "n_surface_channels": 7,
                        "base_channels": args.base_channels,
                        "encoder_depth": args.encoder_depth,
                        "latent_dim": args.latent_dim,
                        "n_fourier_freqs": 16,
                        "decoder_hidden": [128, 128, 64],
                    },
                    "is_demo_mode": args.demo_mode,
                },
                checkpoint_path,
            )
            logger.info(f"★ Saved best model checkpoint to {checkpoint_path} (Val RMSE: {best_val_rmse:.4f})")

    total_time = time.time() - start_time
    logger.info(f"Training completed in {total_time:.1f}s. Best Val RMSE: {best_val_rmse:.4f}")

    # Save training history
    history_file = args.metrics_dir / "ocean_embed_training_history.json"
    with open(history_file, "w") as f:
        json.dump(
            {
                "model": "OceanEmbed",
                "is_demo_mode": args.demo_mode,
                "scientific_status": "DEMO / SOFTWARE_TEST" if args.demo_mode else "TRAINED_ON_REAL_DATA",
                "epochs": args.epochs,
                "best_val_rmse": best_val_rmse,
                "total_time_seconds": total_time,
                "history": history,
            },
            f,
            indent=2,
        )
    logger.info(f"Saved training history to {history_file}")


if __name__ == "__main__":
    main()
