"""
OceanEmbed — Baseline Training Script (V1).

Trains the U-Net baseline model on preprocessed OceanEmbed samples.

Usage:
    python scripts/train/train_baseline.py
    python scripts/train/train_baseline.py --demo-mode  # use synthetic data

Config: configs/training_config.yaml + configs/model_config.yaml
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> float:
    model.train()
    total_loss = 0.0
    n_batches = 0

    for batch in loader:
        inputs = batch["inputs"].to(device)   # (B, T, 7, H, W) or (B, 7, H, W)
        target = batch["target"].to(device)   # (B, 15, H, W)

        # For baseline: use only last timestep inputs
        if inputs.dim() == 5:
            inputs = inputs[:, -1, :, :, :]  # (B, 7, H, W)

        optimizer.zero_grad()
        pred = model(inputs)  # (B, 15, H, W)

        # Mask NaN targets
        valid = torch.isfinite(target)
        loss = ((pred - target) ** 2 * valid.float()).sum() / valid.float().sum().clamp(min=1)

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += loss.item()
        n_batches += 1

    return total_loss / max(n_batches, 1)


@torch.no_grad()
def validate(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> dict[str, float]:
    model.eval()
    all_pred, all_target = [], []

    for batch in loader:
        inputs = batch["inputs"].to(device)
        target = batch["target"].to(device)

        if inputs.dim() == 5:
            inputs = inputs[:, -1, :, :, :]

        pred = model(inputs)
        all_pred.append(pred.cpu().numpy())
        all_target.append(target.cpu().numpy())

    all_pred = np.concatenate(all_pred, axis=0)
    all_target = np.concatenate(all_target, axis=0)

    valid_mask = np.isfinite(all_target) & np.isfinite(all_pred)
    p = all_pred[valid_mask]
    t = all_target[valid_mask]

    if len(p) == 0:
        return {"val_rmse": float("inf"), "val_mae": float("inf")}

    rmse = float(np.sqrt(np.mean((p - t) ** 2)))
    mae = float(np.mean(np.abs(p - t)))
    bias = float(np.mean(p - t))

    return {"val_rmse": rmse, "val_mae": mae, "val_bias": bias}


def main() -> None:
    parser = argparse.ArgumentParser(description="Train OceanEmbed Baseline Model")
    parser.add_argument("--demo-mode", action="store_true", help="Use synthetic demo data")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--checkpoint-dir", default="artifacts/checkpoints")
    args = parser.parse_args()

    # ── Load config ───────────────────────────────────────────────────────────
    import yaml
    with open("configs/training_config.yaml") as f:
        train_cfg = yaml.safe_load(f)

    seed = train_cfg.get("seed", 42)
    set_seed(seed)

    max_epochs = args.epochs or train_cfg.get("max_epochs", 50)
    batch_size = args.batch_size or train_cfg.get("batch_size", 4)
    lr = args.lr or train_cfg["optimizer"]["lr"]
    patience = train_cfg["early_stopping"]["patience"]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Device: {device}")

    # ── Dataset ───────────────────────────────────────────────────────────────
    use_demo = args.demo_mode or not Path("data/processed/train").exists()
    if use_demo:
        logger.warning("Using DEMO / SYNTHETIC dataset. Results are NOT scientific.")
        from src.data.dataset import DemoDataset
        train_ds = DemoDataset(n_samples=100, seed=seed)
        val_ds = DemoDataset(n_samples=20, seed=seed + 1)
    else:
        from src.data.dataset import OceanEmbedDataset
        train_ds = OceanEmbedDataset("data/processed", split="train")
        val_ds = OceanEmbedDataset("data/processed", split="validation")

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size * 2, shuffle=False, num_workers=0)

    logger.info(f"Train: {len(train_ds)} samples | Val: {len(val_ds)} samples")

    # ── Model ─────────────────────────────────────────────────────────────────
    from src.models.baseline import BaselineModel
    model = BaselineModel(
        in_channels=7,
        out_depths=15,
        base_channels=32,
        encoder_depth=4,
    ).to(device)
    logger.info(f"Parameters: {model.count_parameters():,}")

    # ── Optimizer + Scheduler ─────────────────────────────────────────────────
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=lr,
        weight_decay=train_cfg["optimizer"]["weight_decay"],
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=max_epochs, eta_min=1e-6
    )

    # ── Training loop ─────────────────────────────────────────────────────────
    checkpoint_dir = Path(args.checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    best_val_rmse = float("inf")
    patience_counter = 0
    history: list[dict] = []

    for epoch in range(1, max_epochs + 1):
        t0 = time.time()
        train_loss = train_one_epoch(model, train_loader, optimizer, torch.nn.MSELoss(), device)
        val_metrics = validate(model, val_loader, device)
        scheduler.step()
        dt = time.time() - t0

        val_rmse = val_metrics["val_rmse"]
        record = {"epoch": epoch, "train_loss": train_loss, **val_metrics, "lr": scheduler.get_last_lr()[0]}
        history.append(record)

        logger.info(
            f"Epoch {epoch:3d}/{max_epochs} | "
            f"train_loss={train_loss:.4f} | "
            f"val_rmse={val_rmse:.4f} | "
            f"val_mae={val_metrics.get('val_mae', float('nan')):.4f} | "
            f"time={dt:.1f}s"
        )

        if val_rmse < best_val_rmse:
            best_val_rmse = val_rmse
            patience_counter = 0
            ckpt = {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_rmse": val_rmse,
                "demo_mode": use_demo,
            }
            torch.save(ckpt, checkpoint_dir / "baseline_best.pt")
            logger.info(f"  ✓ New best: val_rmse={val_rmse:.4f}")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"Early stopping at epoch {epoch} (patience={patience}).")
                break

    torch.save(model.state_dict(), checkpoint_dir / "baseline_last.pt")

    # Save training history
    metrics_dir = Path("artifacts/metrics")
    metrics_dir.mkdir(parents=True, exist_ok=True)
    with open(metrics_dir / "baseline_training_history.json", "w") as f:
        json.dump({"demo_mode": use_demo, "history": history, "best_val_rmse": best_val_rmse}, f, indent=2)

    demo_note = " [DEMO/SYNTHETIC — not a scientific result]" if use_demo else " [REAL DATA]"
    logger.info(f"Training complete. Best val_rmse={best_val_rmse:.4f}{demo_note}")


if __name__ == "__main__":
    main()
