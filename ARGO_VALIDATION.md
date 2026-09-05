# OceanEmbed — ARGO Validation Protocol

## Design Principle

ARGO profiles used for independent validation are NEVER used during training.
The split is:
- Training/validation/test: GLORYS12V1 reanalysis, 1993–2022
- ARGO validation: Independent in-situ profiles, 2019–2022

## Protocol

For each valid ARGO profile in the validation set:

1. **Read profile**: location (lat, lon), time (JULD), pressure levels, temperature
2. **QC filter**: retain PROFILE_STATUS_FLAG=A/D, TEMP_QC=1, PRES_QC=1
3. **Pressure to depth**: `z ≈ pressure (dbar)` (within 2% error for 0–1000 m)
4. **Find model input**: obtain surface satellite observations for same date/location
5. **Run OceanEmbed**: use nearest grid point, same date
6. **Query at ARGO depths**: use continuous depth decoder (key feature)
7. **Compare**: T_predicted vs T_observed at each depth
8. **Compute metrics**: RMSE, MAE, Bias, correlation per profile
9. **Aggregate**: by depth band, region (Bay of Bengal / Arabian Sea)

## Access

### INCOIS ERDDAP

```python
import requests

url = (
    "https://erddap.incois.gov.in/erddap/tabledap/ArgoProfilesIS.csv"
    "?JULD,LATITUDE,LONGITUDE,PRES,TEMP,PSAL,PROFILE_STATUS_FLAG"
    "&LATITUDE>=5&LATITUDE<=30&LONGITUDE>=45&LONGITUDE<=105"
    "&JULD>=2021-01-01T00:00:00Z&JULD<=2022-12-31T23:59:59Z"
    "&PROFILE_STATUS_FLAG=A"
)
response = requests.get(url)
```

### argopy (Global GDAC fallback)

```python
import argopy
loader = argopy.DataFetcher().region([45, 105, 5, 30, 0, 2000, "2021-01", "2023-01"])
ds = loader.to_xarray()
```

## Status

**RESULT NOT YET AVAILABLE** — Blocked pending:
1. Download of real ARGO profiles
2. Trained OceanEmbed model

When complete, results will be stored at:
- `artifacts/metrics/argo_validation_metrics.json`
