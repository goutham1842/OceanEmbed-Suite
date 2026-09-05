"""
OceanEmbed — ARGO Profile Download Script.

Downloads ARGO float profiles for the Indian Ocean via:
1. INCOIS ERDDAP REST API (primary source)
2. argopy library as fallback (GDAC global data)

Used ONLY for independent validation (not training).

Usage:
    python scripts/download/download_argo.py --start 2021-01-01 --end 2022-12-31
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("data/raw/argo")

# INCOIS ERDDAP configuration (public, no credentials required)
INCOIS_ERDDAP_BASE = "https://erddap.incois.gov.in/erddap"
INCOIS_DATASET_ID = "ArgoProfilesIS"


def download_argo_incois_erddap(
    start_date: str,
    end_date: str,
    output_dir: Path = OUTPUT_DIR,
) -> Path:
    """Download ARGO profiles from INCOIS ERDDAP.

    Domain: North Indian Ocean (5–30°N, 45–105°E)
    Only Adjusted/Delayed-mode profiles are downloaded.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    fname = f"argo_incois_{start_date}_{end_date}.csv"
    output_path = output_dir / fname

    if output_path.exists():
        logger.info(f"File already exists: {output_path}. Skipping.")
        return output_path

    # Build ERDDAP tabledap query
    url = (
        f"{INCOIS_ERDDAP_BASE}/tabledap/{INCOIS_DATASET_ID}.csv"
        f"?JULD,LATITUDE,LONGITUDE,PRES,TEMP,PSAL,PROFILE_STATUS_FLAG"
        f"&LATITUDE%3E=5&LATITUDE%3C=30"
        f"&LONGITUDE%3E=45&LONGITUDE%3C=105"
        f"&JULD%3E={start_date}T00:00:00Z&JULD%3C={end_date}T23:59:59Z"
        f"&PROFILE_STATUS_FLAG=%22A%22"
    )

    logger.info(f"Querying INCOIS ERDDAP: {url[:120]}...")

    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(response.text)

        n_lines = response.text.count("\n")
        logger.info(f"Downloaded {n_lines} records → {output_path}")
        return output_path

    except requests.exceptions.ConnectionError:
        logger.warning(
            "Could not connect to INCOIS ERDDAP. "
            "Check internet connection or try argopy fallback."
        )
        return _download_argo_argopy_fallback(start_date, end_date, output_dir)

    except Exception as e:
        logger.error(f"INCOIS ERDDAP download failed: {e}")
        logger.info("Trying argopy fallback...")
        return _download_argo_argopy_fallback(start_date, end_date, output_dir)


def _download_argo_argopy_fallback(
    start_date: str,
    end_date: str,
    output_dir: Path,
) -> Path:
    """Fallback: download via argopy library from Global ARGO GDAC."""
    try:
        import argopy
    except ImportError:
        raise ImportError(
            "argopy package not installed. Run: pip install argopy\n"
            "Also check INCOIS ERDDAP connectivity."
        )

    fname = f"argo_gdac_{start_date}_{end_date}.nc"
    output_path = output_dir / fname

    if output_path.exists():
        logger.info(f"File already exists: {output_path}. Skipping.")
        return output_path

    logger.info("Fetching ARGO data via argopy (GDAC global archive)...")

    # region: [lon_min, lon_max, lat_min, lat_max, pres_min, pres_max, date_min, date_max]
    start_ym = start_date[:7]
    end_ym = end_date[:7]

    loader = argopy.DataFetcher().region([45, 105, 5, 30, 0, 2000, start_ym, end_ym])
    ds = loader.to_xarray()
    ds.to_netcdf(output_path)
    logger.info(f"argopy download complete → {output_path}")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Download ARGO profiles for North Indian Ocean")
    parser.add_argument("--start", default="2021-01-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default="2022-12-31", help="End date YYYY-MM-DD")
    parser.add_argument(
        "--generate-mock", action="store_true",
        help="Generate synthetic mock ARGO float acquisition data for offline pipeline validation"
    )
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))

    args = parser.parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.generate_mock:
        from src.evaluation.argo_validation import generate_synthetic_argo_profiles
        profiles = generate_synthetic_argo_profiles(num_profiles=15)
        mock_file = out_dir / "argo_incois_mock_sample.json"
        with open(mock_file, "w", encoding="utf-8") as f:
            import json
            json.dump([
                {
                    "platform_id": p.platform_id,
                    "cycle_number": p.cycle_number,
                    "lat": p.lat,
                    "lon": p.lon,
                    "date": p.date,
                    "depths": p.depths.tolist(),
                    "temperatures": p.temperatures.tolist(),
                } for p in profiles
            ], f, indent=2)
        logger.info(f"SUCCESS: Mock ARGO acquisition sample staged at {mock_file}")
        return

    logger.info(
        "ARGO download is for INDEPENDENT VALIDATION only.\n"
        "These profiles must NOT be used during training."
    )

    try:
        path = download_argo_incois_erddap(args.start, args.end, out_dir)
        logger.info(f"SUCCESS: {path}")
    except Exception as e:
        logger.error(f"ARGO download failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
