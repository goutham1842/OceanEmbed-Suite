"""
OceanEmbed — GLORYS12V1 Download Script.

Downloads GLORYS12V1 subsurface temperature for the North Indian Ocean
using the official Copernicus Marine Python API (copernicusmarine).

Credentials are read from environment variables:
  COPERNICUSMARINE_SERVICE_USERNAME
  COPERNICUSMARINE_SERVICE_PASSWORD

Never hard-code credentials. See .env.example.

Usage:
    python scripts/download/download_glorys.py --start 2020-01-01 --end 2020-01-07
    python scripts/download/download_glorys.py --test-slice
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
DATASET_ID = "cmems_mod_glo_phy_my_0.083deg_P1D-m"
PRODUCT_ID = "GLOBAL_MULTIYEAR_PHY_001_030"
VARIABLES = ["thetao"]  # subsurface temperature (°C)

DOMAIN = {
    "lat_min": 5.0,  "lat_max": 30.0,
    "lon_min": 45.0, "lon_max": 105.0,
    "depth_min": 0.0, "depth_max": 1000.0,
}

OUTPUT_DIR = Path("data/raw/glorys")


def check_credentials() -> tuple[str, str]:
    """Read CMEMS credentials from environment variables.

    Returns (username, password) or raises if not set.
    """
    username = os.environ.get("COPERNICUSMARINE_SERVICE_USERNAME", "")
    password = os.environ.get("COPERNICUSMARINE_SERVICE_PASSWORD", "")

    if not username or not password:
        raise EnvironmentError(
            "CMEMS credentials not found.\n"
            "Set environment variables:\n"
            "  COPERNICUSMARINE_SERVICE_USERNAME=<your_username>\n"
            "  COPERNICUSMARINE_SERVICE_PASSWORD=<your_password>\n"
            "Register at https://marine.copernicus.eu/"
        )
    return username, password


def download_glorys(start_date: str, end_date: str, output_dir: Path = OUTPUT_DIR) -> Path:
    """Download GLORYS12V1 subsurface temperature.

    Args:
        start_date: "YYYY-MM-DD"
        end_date:   "YYYY-MM-DD"
        output_dir: directory to save the NetCDF file

    Returns:
        Path to downloaded file
    """
    check_credentials()

    try:
        import copernicusmarine
    except ImportError:
        raise ImportError(
            "copernicusmarine package not installed.\n"
            "Run: pip install copernicusmarine"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    fname = f"glorys_NIO_{start_date}_{end_date}.nc"
    output_path = output_dir / fname

    if output_path.exists():
        logger.info(f"File already exists: {output_path}. Skipping download.")
        return output_path

    logger.info(
        f"Downloading GLORYS12V1: {start_date} to {end_date}\n"
        f"  Dataset: {DATASET_ID}\n"
        f"  Variables: {VARIABLES}\n"
        f"  Domain: {DOMAIN['lat_min']}–{DOMAIN['lat_max']}°N, "
        f"{DOMAIN['lon_min']}–{DOMAIN['lon_max']}°E\n"
        f"  Depth: {DOMAIN['depth_min']}–{DOMAIN['depth_max']} m\n"
        f"  Output: {output_path}"
    )

    copernicusmarine.subset(
        dataset_id=DATASET_ID,
        variables=VARIABLES,
        minimum_latitude=DOMAIN["lat_min"],
        maximum_latitude=DOMAIN["lat_max"],
        minimum_longitude=DOMAIN["lon_min"],
        maximum_longitude=DOMAIN["lon_max"],
        minimum_depth=DOMAIN["depth_min"],
        maximum_depth=DOMAIN["depth_max"],
        start_datetime=f"{start_date}T00:00:00",
        end_datetime=f"{end_date}T23:59:59",
        output_filename=fname,
        output_directory=str(output_dir),
        force_download=False,
    )

    logger.info(f"Download complete: {output_path}")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Download GLORYS12V1 for North Indian Ocean")
    parser.add_argument("--start", default="2020-01-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default="2020-01-31", help="End date YYYY-MM-DD")
    parser.add_argument(
        "--test-slice", action="store_true",
        help="Download a minimal 7-day test slice (Jan 2020)"
    )
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))

    args = parser.parse_args()

    if args.test_slice:
        start, end = "2020-01-01", "2020-01-07"
        logger.info("Test slice mode: downloading 7 days only.")
    else:
        start, end = args.start, args.end

    try:
        path = download_glorys(start, end, Path(args.output_dir))
        logger.info(f"SUCCESS: {path}")
    except EnvironmentError as e:
        logger.error(f"CREDENTIAL BLOCKER:\n{e}")
        logger.info(
            "All other pipeline components continue to work without data.\n"
            "See ROADMAP.md for credential setup instructions."
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Download failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
