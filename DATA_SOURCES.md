# OceanEmbed — Data Sources

See [`data_sources.yaml`](data_sources.yaml) for the machine-readable registry.

## Access Requirements

| Dataset | Provider | Credential Required | Role |
|---|---|---|---|
| GLORYS12V1 | CMEMS | Yes (CMEMS account) | Training target |
| OSTIA SST | CMEMS | Yes | Primary SST input |
| ESA CCI SST | C3S | Yes (CDS API key) | Alternative SST |
| CMEMS SSS L4 | CMEMS | Yes | Primary SSS input |
| SMOS CATDS SSS | CATDS | No | Alternative SSS |
| DUACS SLA | CMEMS | Yes | SSH + currents |
| ERA5 Winds | CDS | Yes | Primary winds |
| ASCAT Winds | EUMETSAT | No | Alternative winds |
| INCOIS ARGO | INCOIS | No | Independent validation |
| Argo GDAC | IFREMER | No | Alternative ARGO access |

## How to Get Credentials

### CMEMS (Required for GLORYS, OSTIA, DUACS, SSS)
1. Register at https://marine.copernicus.eu/
2. Activate your account
3. Set in `.env`:
   ```
   COPERNICUSMARINE_SERVICE_USERNAME=your_username
   COPERNICUSMARINE_SERVICE_PASSWORD=your_password
   ```

### CDS API Key (Required for ERA5)
1. Register at https://cds.climate.copernicus.eu/
2. Follow https://cds.climate.copernicus.eu/api-how-to
3. Set in `.env`:
   ```
   CDSAPI_KEY=your-key
   CDSAPI_URL=https://cds.climate.copernicus.eu/api/v2
   ```

## Data Access Status

| Dataset | Status |
|---|---|
| GLORYS12V1 | RESULT NOT YET AVAILABLE — requires CMEMS credentials |
| OSTIA SST | RESULT NOT YET AVAILABLE — requires CMEMS credentials |
| CMEMS SSS | RESULT NOT YET AVAILABLE — requires CMEMS credentials |
| DUACS SLA | RESULT NOT YET AVAILABLE — requires CMEMS credentials |
| ERA5 Winds | RESULT NOT YET AVAILABLE — requires CDS API key |
| INCOIS ARGO | RESULT NOT YET AVAILABLE — public but awaiting pipeline execution |

## Download Scripts

Once credentials are in place, run:

```bash
# GLORYS12V1 (training target)
python scripts/download/download_glorys.py --start 2020-01-01 --end 2020-01-31

# OSTIA SST
python scripts/download/download_sst.py --start 2020-01-01 --end 2020-01-31

# DUACS SLA + Currents
python scripts/download/download_sla.py --start 2020-01-01 --end 2020-01-31

# CMEMS SSS
python scripts/download/download_sss.py --start 2020-01-01 --end 2020-01-31

# ERA5 Winds
python scripts/download/download_winds.py --start 2020-01-01 --end 2020-01-31

# ARGO Validation Profiles
python scripts/download/download_argo.py --start 2021-01-01 --end 2022-12-31
```

## Spatial Subset

All datasets are subsetted as early as possible:
- Latitude: 5°N – 30°N
- Longitude: 45°E – 105°E

## Leakage Prevention

- Normalization statistics computed from training data only (1993–2018)
- ARGO validation profiles kept completely separate from training
- Chronological split: train/val/test in time order
