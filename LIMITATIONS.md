# OceanEmbed — Limitations

## Data Access Limitations

**CMEMS Credentials Required**  
GLORYS12V1, OSTIA SST, CMEMS SSS, and DUACS SLA all require a Copernicus Marine
Service account. Until these credentials are provided, training data cannot be
downloaded and the model cannot be trained on real data.

**CDS API Key Required**  
ERA5 surface wind data requires a Copernicus Climate Data Store API key.

## Hardware Limitations

**No GPU Available**  
The current development system is CPU-only (PyTorch 2.8.0+cpu, 12 cores).
Training times will be significantly longer than on GPU-equipped hardware.
Model complexity has been adjusted (batch_size=4, smaller architectures for testing)
but full-resolution training over multiple years of data will be impractical on CPU.

**Memory / Storage**  
GLORYS12V1 over the full training period (1993–2018) for the North Indian Ocean
region may require ~50–200 GB storage. Dask lazy loading is used to avoid
loading full datasets into RAM.

## Model Limitations

**Training Data Limitations**  
If real data is unavailable, the model cannot produce scientifically meaningful
predictions. Demo mode produces synthetic outputs for software testing only.

**Uncertainty Calibration**  
The heteroscedastic uncertainty is a predictive variance estimate. It is NOT
calibrated to frequentist probability unless explicitly evaluated on held-out data.
Calibration evaluation requires held-out ARGO profiles.

**Continuous Depth Accuracy**  
The continuous depth decoder interpolates between training depth levels.
Prediction quality may degrade at depths poorly sampled by GLORYS12V1.

**Regional Conditioning**  
Regional conditioning adds a learned embedding per ocean basin. It does NOT
guarantee improved performance in all scenarios; performance must be measured.

**Temporal Context**  
A 3-day window is used. Longer oceanographic phenomena (MJO, seasonal cycles)
are captured only partially. ENSO and interannual variability require longer
context or explicit seasonal encoding.

**Physics-Informed Loss**  
The thermocline regularization is configurable and ablated experimentally.
Its scientific benefit is a testable hypothesis, not a guaranteed improvement.

## Scientific Limitations

**No Causal Claims**  
OceanEmbed learns correlations between surface observations and subsurface
temperature. No causal mechanism is claimed.

**Extrapolation Risk**  
Predictions outside the training distribution (unusual ocean states, extreme
weather events) may be unreliable. Uncertainty estimates may not capture
out-of-distribution scenarios.

**ARGO Validation Coverage**  
ARGO float coverage is uneven. Some regions (open ocean Bay of Bengal, western
Arabian Sea) may have fewer validation profiles.

**Not an Operational System**  
OceanEmbed is a research prototype for SIH26066. It is NOT validated for
operational oceanographic use.
