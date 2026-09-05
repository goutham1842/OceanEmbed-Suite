"""
OceanEmbed — ARGO Independent Validation CLI Script.

Validates the trained OceanEmbed model or engine against independent ARGO float profiles.
Evaluates at continuous float observation depths.

Usage:
    python scripts/evaluate/validate_argo.py --demo-mode
    python scripts/evaluate/validate_argo.py --data-dir data/raw/argo --checkpoint artifacts/checkpoints/ocean_embed_best.pt
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.argo_validation import (
    evaluate_profiles_against_engine,
    generate_synthetic_argo_profiles,
    load_argo_profiles_from_dir,
)
from src.inference.engine import OceanEmbedEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("validate_argo")


def parse_args():
    parser = argparse.ArgumentParser(description="Validate OceanEmbed against ARGO float profiles")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "raw" / "argo",
        help="Directory containing ARGO float NetCDF/JSON files",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "checkpoints" / "ocean_embed_best.pt",
        help="Path to trained OceanEmbed model checkpoint",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "artifacts" / "metrics",
        help="Directory to save evaluation results",
    )
    parser.add_argument(
        "--demo-mode",
        action="store_true",
        help="Force DEMO / synthetic mode for software pipeline verification",
    )
    parser.add_argument(
        "--num-synthetic",
        type=int,
        default=25,
        help="Number of synthetic profiles to generate if in demo mode",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Initializing OceanEmbed inference engine...")
    engine = OceanEmbedEngine(checkpoint_path=args.checkpoint)

    profiles = []
    if not args.demo_mode and args.data_dir.exists():
        logger.info(f"Scanning for real ARGO profiles in {args.data_dir}...")
        profiles = load_argo_profiles_from_dir(args.data_dir)

    if not profiles:
        logger.info(
            "No real ARGO profiles found or --demo-mode specified. "
            f"Generating {args.num_synthetic} synthetic ARGO profiles for software verification..."
        )
        profiles = generate_synthetic_argo_profiles(num_profiles=args.num_synthetic)

    logger.info(f"Validating {len(profiles)} profiles against OceanEmbed engine...")
    results = evaluate_profiles_against_engine(profiles, engine)

    # Save results
    output_file = args.output_dir / "argo_validation_report.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Saved validation report to: {output_file}")
    logger.info("=" * 60)
    logger.info(f"ARGO Validation Summary: Status={results.get('status')}")
    logger.info(f"Data type: {results.get('data_type')}")
    logger.info(f"Scientific validity: {results.get('scientific_validity')}")
    overall = results.get("overall_metrics", {})
    logger.info(
        f"Overall RMSE: {overall.get('rmse', 'N/A'):.4f} °C | "
        f"MAE: {overall.get('mae', 'N/A'):.4f} °C | "
        f"Bias: {overall.get('bias', 'N/A'):.4f} °C | "
        f"Pearson r: {overall.get('pearson_r', 'N/A'):.4f}"
    )

    bands = results.get("depth_band_metrics", {})
    for b_name, b_m in bands.items():
        logger.info(f"  Band {b_name:10s} -> RMSE: {b_m.get('rmse', 'N/A'):.4f} °C, MAE: {b_m.get('mae', 'N/A'):.4f} °C")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
