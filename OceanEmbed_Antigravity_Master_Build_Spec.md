# OceanEmbed — Antigravity Master Build Specification
## Smart India Hackathon 2026 | SIH26066

**Source of truth for the autonomous Antigravity coding agent.**

The agent must build this project inside the current workspace. It must create files, folders, code, configuration, tests, documentation, data pipelines, model implementations, backend, and frontend itself. Do not merely explain how to build them.

---

## 1. Project

**Name:** OceanEmbed

**Title:** OceanEmbed — Continuous, Uncertainty-Aware and Missing-Data-Resilient Subsurface Ocean Temperature Reconstruction

**SIH:** SIH26066

**Organization:** Ministry of Earth Sciences / INCOIS

**Domain:** Software / Space Technology

### Objective

Build an end-to-end scientifically defensible prototype that reconstructs subsurface ocean temperature over the North Indian Ocean from surface satellite observations.

Required region:

- Latitude: 5°N–30°N
- Longitude: 45°E–105°E

Required grid:

- 0.25° × 0.25°
- Daily

Required output depths:

`0, 5, 10, 20, 30, 50, 75, 100, 125, 150, 200, 300, 500, 700, 1000 m`

Surface inputs:

- SST
- SSS
- SSH/SLA
- surface current U
- surface current V
- surface wind U
- surface wind V

Primary training target:

- GLORYS12V1 subsurface temperature

Independent validation:

- INCOIS / Indian Ocean ARGO observations

---

## 2. Central research hypothesis

Learn a continuous latent representation of the hidden ocean state from multimodal surface observations.

Conceptually:

`T = f(SST, SSS, SSH, U, V, windU, windV, latitude, longitude, time, depth)`

The final model must answer:

`T(latitude, longitude, time, depth)`

for arbitrary depth between 0 and 1000 m, not only the 15 fixed SIH depths.

Core contribution:

**Continuous Depth-Conditioned Ocean Representation**

Additional contributions:

1. explicit missing-observation masks;
2. uncertainty estimation;
3. temporal context;
4. region-aware learning for Bay of Bengal and Arabian Sea;
5. thermocline-aware analysis;
6. scientifically justified physics-informed regularization where useful;
7. independent ARGO validation.

Do not call the project simply “NeRF”. Coordinate-conditioned neural representations may inspire the design, but this is an ocean reconstruction system.

---

## 3. Novelty rules

Generic satellite-based subsurface reconstruction is NOT claimed as novel.

Do not claim “first ever”, “world's first”, “no existing system”, or superiority without experimental evidence.

Position the contribution as the integrated combination of:

- continuous-depth querying;
- explicit uncertainty;
- missing-data resilience;
- North Indian Ocean focus;
- independent ARGO validation;
- interactive scientific inference.

The research hypothesis must be presented as a testable hypothesis, not a guaranteed result.

---

## 4. Dataset plan

Create `data_sources.yaml` and `DATA_SOURCES.md`.

For every dataset record:

- name
- provider
- official URL
- product/dataset ID if available
- variables
- spatial resolution
- temporal resolution
- vertical information
- coverage
- role
- access/download method
- preprocessing
- licensing/access notes
- whether it is input, target, validation, or auxiliary

### Core datasets

#### GLORYS12V1
Provider: Copernicus Marine.

Product: `GLOBAL_MULTIYEAR_PHY_001_030`

Role: primary 3D training target.

Use subsurface temperature and depth levels. Supporting variables may be used for analysis where scientifically justified.

#### OSTIA SST
Role: primary daily SST input.

#### ESA SST CCI/C3S
Role: historical/alternative SST experiments.

#### Copernicus Multi-Observation SSS
Role: primary daily SSS input.

#### SMOS CATDS SSS
Role: alternative satellite SSS / robustness experiment.

#### DUACS L4 Sea Level / SLA
Role: SSH/SLA input and, where appropriate, associated geostrophic surface currents.

#### Copernicus surface winds
Role: surface wind U/V input. Aggregate appropriately to daily values.

#### Scatterometer wind products
Role: alternative satellite wind/robustness experiment.

#### INCOIS / Indian Ocean ARGO
Role: independent validation.

ARGO must not be used as independent validation if the same profiles were used for training.

---

## 5. Data acquisition

Implement reproducible download/access scripts using official documented mechanisms such as Copernicus Marine APIs/Toolbox and INCOIS ERDDAP.

Never invent URLs or credentials.

If authentication is required:

1. create the complete downloader;
2. document what credentials/access are required;
3. read secrets from environment variables;
4. never hard-code credentials;
5. continue all other work that does not require those credentials.

Do not download entire global products unnecessarily. Spatially and temporally subset to the North Indian Ocean as early as practical.

Start with a small real-data slice to prove the pipeline before scaling.

---

## 6. Data architecture

Create automatically:

```text
data/
├── raw/
│   ├── satellite/
│   │   ├── sst/
│   │   ├── sss/
│   │   ├── ssh/
│   │   ├── currents/
│   │   └── winds/
│   ├── glorys/
│   └── argo/
├── interim/
│   ├── harmonized/
│   └── regridded/
└── processed/
    ├── train/
    ├── validation/
    └── test/
```

Do not commit large NetCDF/Zarr files to Git.

Create a proper `.gitignore`.

---

## 7. Harmonization pipeline

Implement:

1. spatial subsetting;
2. coordinate normalization;
3. longitude normalization;
4. time normalization;
5. unit normalization;
6. quality control;
7. invalid-value handling;
8. explicit missing-data masks;
9. spatial regridding;
10. daily temporal harmonization;
11. common 0.25° grid;
12. aligned model-ready samples.

Use xarray, numpy, scipy and Dask where appropriate.

Document every regridding/interpolation choice.

Avoid loading huge global datasets into RAM.

---

## 8. Leakage prevention

Use chronological train/validation/test separation.

Do not randomly split pixels from the same dates in a way that leaks information.

Determine exact split periods from actual dataset availability and record them in configuration.

Fit normalization statistics only on training data.

Keep independent ARGO validation separate.

Never use validation/test data to tune preprocessing.

---

## 9. Model development sequence

Do not immediately build the most complex model.

### Version 1 — Baseline

Input:

7 surface channels:

`SST, SSS, SSH, current_U, current_V, wind_U, wind_V`

Output:

15 standard-depth temperature maps.

Use a strong CNN/U-Net-style encoder-decoder.

Generate actual baseline metrics from real data.

### Version 2

Add temporal context.

### Version 3

Add missing-data masks.

### Version 4

Add uncertainty estimation.

### Version 5

Add continuous depth-conditioned decoding.

### Version 6

Add region-aware conditioning.

### Version 7

Add scientifically justified physics/thermocline components.

Make all components modular and ablatable.

---

## 10. Final OceanEmbed architecture

Implement:

```text
Surface observations
        +
Missingness masks
        +
Coordinates
        +
Temporal context
        ↓
Multimodal surface encoder
        ↓
Spatial-temporal features
        ↓
Ocean latent embedding
        ↓
Continuous depth-conditioned decoder
        ↓
Temperature mean + uncertainty
```

Conceptually:

```text
E = Encoder(X, mask, location, time)

T(z) = Decoder(E, z, location, time)

U(z) = UncertaintyHead(E, z, mask)
```

where `z` is continuous depth.

---

## 11. Continuous depth

The final decoder must accept a depth query.

A suitable implementation may use:

- normalized depth;
- Fourier/positional encoding;
- conditioning on the learned ocean embedding;
- a continuous decoder.

Support arbitrary depths such as:

- 37 m
- 82.5 m
- 137 m
- 173.5 m
- 250 m
- 421 m
- 650 m
- 873 m

as well as every SIH standard depth.

Support only:

`0 ≤ depth ≤ 1000 m`

The 15 SIH outputs are generated by querying this continuous representation at the required depths.

---

## 12. Temporal context

Where computationally feasible, use previous daily observations, initially with a small configurable window.

Example:

`t-2, t-1, t → prediction at t`

Avoid temporal leakage.

---

## 13. Missing observations

Provide explicit validity masks for every modality.

Example:

```text
SST + SST_mask
SSS + SSS_mask
SSH + SSH_mask
current_U + current_U_mask
current_V + current_V_mask
wind_U + wind_U_mask
wind_V + wind_V_mask
```

Run controlled experiments:

1. all inputs available;
2. SSS missing;
3. SSH missing;
4. wind missing;
5. currents missing;
6. multiple modalities missing.

Hypothesis to test:

Prediction remains usable while uncertainty increases.

Only report this as a result if measured.

---

## 14. Uncertainty

Implement a defensible predictive uncertainty method.

A candidate is heteroscedastic regression:

```text
model → mean μ
model → log variance
```

with an appropriate probabilistic loss such as Gaussian NLL if assumptions are acceptable.

Return:

- predicted temperature;
- uncertainty;
- confidence representation;
- metadata.

Document the meaning and limitations of uncertainty.

Evaluate calibration where possible.

Never fabricate confidence.

---

## 15. Regional learning

Support:

- Bay of Bengal;
- Arabian Sea.

Prefer shared backbone + regional conditioning.

Measure regional performance rather than assuming it.

---

## 16. Thermocline and physics

Calculate vertical temperature gradient:

`dT/dz`

Implement a documented thermocline detection method suitable for the available profile resolution.

Do not impose simplistic monotonic temperature assumptions.

Calculate:

- predicted thermocline depth;
- reference thermocline depth;
- thermocline depth error.

Any physics-informed loss must be configurable, scientifically justified, and included in ablations.

---

## 17. Training

Use PyTorch.

Implement:

- configurable batch size;
- learning rate;
- optimizer;
- scheduler;
- mixed precision when supported;
- checkpointing;
- early stopping;
- reproducible seeds;
- logging;
- experiment configuration;
- resume capability.

Inspect available CPU/GPU/RAM/storage and automatically select a sensible development configuration.

If no GPU is available, provide a small CPU-friendly configuration.

---

## 18. Evaluation

Implement:

- RMSE;
- MAE;
- Bias;
- Pearson correlation;
- R² where appropriate;
- depth-wise error;
- regional error;
- temporal error;
- thermocline depth error;
- uncertainty calibration metrics.

Evaluate at:

- all 15 SIH depths;
- arbitrary depth queries;
- depth bands:

```text
0–100 m
100–300 m
300–500 m
500–700 m
700–1000 m
```

---

## 19. ARGO validation

Build a separate independent validation pipeline.

For each valid ARGO profile:

1. read location;
2. read time;
3. apply QC;
4. obtain corresponding surface inputs;
5. run OceanEmbed;
6. query the model at ARGO observation depths;
7. compare predicted and observed temperature;
8. calculate metrics;
9. group by depth and region.

Metrics:

- RMSE;
- MAE;
- Bias;
- correlation;
- thermocline error where valid.

Do not use the same ARGO observations for training and independent validation.

---

## 20. Ablation experiments

Implement and record:

```text
Baseline
Baseline + temporal context
Baseline + missing masks
Baseline + uncertainty
Baseline + continuous depth
Baseline + region conditioning
Baseline + physics/thermocline
Final OceanEmbed
```

The exact sequence may be adjusted if dependencies require it.

Store configuration and results for every experiment.

Only claim improvement when measured.

---

## 21. Scientific plots

Generate actual plots from real data/model outputs:

1. SST map
2. SSS map
3. SSH/SLA map
4. surface wind/current maps
5. predicted temperature maps at standard depths
6. arbitrary-depth temperature map
7. vertical temperature profiles
8. predicted vs ARGO profiles
9. error maps
10. RMSE vs depth
11. MAE vs depth
12. Bias vs depth
13. correlation vs depth
14. thermocline comparison
15. uncertainty maps
16. missing-data robustness
17. Bay of Bengal vs Arabian Sea
18. ablation study

Never generate fake scientific figures.

---

## 22. Backend

Use FastAPI.

Implement:

```text
GET /api/health
GET /api/metadata
GET /api/dates
GET /api/depths
GET /api/prediction
GET /api/profile
GET /api/metrics
GET /api/argo-comparison
```

Prediction must support:

- date;
- latitude;
- longitude;
- depth;
- modality availability/masks.

Return actual model outputs.

---

## 23. Frontend

Use:

- React;
- Vite;
- Tailwind CSS;
- Plotly or equivalent;
- Leaflet/MapLibre where appropriate.

Build a professional scientific dashboard with:

### Map

North Indian Ocean prediction map.

### Controls

- date;
- depth slider 0–1000 m;
- latitude/longitude;
- region.

### Arbitrary depth

User can request values such as 137 m.

### Profile

Show:

- predicted temperature;
- uncertainty;
- ARGO observed profile when available.

### Missing-data demo

Toggle:

- SST;
- SSS;
- SSH;
- currents;
- winds.

The UI must invoke the real model under the corresponding missing-input condition. Do not fake the effect.

### Metrics

Display actual experiment metrics.

### Thermocline

Display actual predicted/reference thermocline depth and error.

### Regional comparison

Compare Bay of Bengal and Arabian Sea.

---

## 24. Demo mode

If real model outputs are unavailable, create a clearly labelled:

`DEMO / SYNTHETIC`

mode for software/UI testing only.

Rules:

- deterministic synthetic values;
- visible DEMO/SYNTHETIC label;
- never use synthetic data as scientific evidence;
- never display synthetic metrics as real results;
- automatically prefer REAL mode once real outputs exist.

---

## 25. Repository structure

Create and maintain a clean structure similar to:

```text
OceanEmbed/
├── README.md
├── ARCHITECTURE.md
├── DATA_SOURCES.md
├── MODEL.md
├── TRAINING.md
├── EVALUATION.md
├── ARGO_VALIDATION.md
├── DEMO.md
├── LIMITATIONS.md
├── RESEARCH_NOVELTY.md
├── ROADMAP.md
├── data_sources.yaml
├── requirements.txt
├── .env.example
├── .gitignore
├── configs/
│   ├── config.yaml
│   ├── data_config.yaml
│   ├── model_config.yaml
│   └── training_config.yaml
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── scripts/
│   ├── download/
│   ├── preprocess/
│   ├── train/
│   └── evaluate/
├── src/
│   ├── data/
│   ├── models/
│   ├── training/
│   ├── evaluation/
│   └── inference/
├── backend/
├── frontend/
├── notebooks/
├── tests/
└── artifacts/
    ├── figures/
    ├── metrics/
    └── checkpoints/
```

The agent may improve the exact structure if technically justified.

---

## 26. Documentation

Create and maintain:

- `README.md`
- `ARCHITECTURE.md`
- `DATA_SOURCES.md`
- `MODEL.md`
- `TRAINING.md`
- `EVALUATION.md`
- `ARGO_VALIDATION.md`
- `DEMO.md`
- `LIMITATIONS.md`
- `RESEARCH_NOVELTY.md`
- `ROADMAP.md`

Documentation must describe what was actually implemented, not planned features presented as completed.

---

## 27. Testing

Create tests for:

- grid generation;
- coordinate handling;
- time handling;
- regridding;
- normalization;
- missing masks;
- depth encoding;
- arbitrary depth queries;
- model forward pass;
- uncertainty output;
- metrics;
- thermocline detection;
- ARGO matching;
- API endpoints.

Run tests and fix failures.

---

## 28. Code quality

Use:

- clear modular code;
- type hints where useful;
- logging;
- configuration-driven paths;
- reproducible scripts;
- graceful error handling.

Do not use giant monolithic scripts.

Do not use hard-coded credentials.

Do not create meaningless placeholder implementations.

---

## 29. Execution phases

### Phase 1 — Environment and repository

Inspect:

- OS;
- Python;
- Node/npm;
- Git;
- CPU;
- RAM;
- GPU/CUDA;
- storage.

Then initialize the repository and create the project structure.

### Phase 2 — Data framework

Implement metadata, download/access framework, preprocessing, QC, harmonization, regridding and sample generation.

### Phase 3 — Small real-data slice

Acquire a manageable real-data subset for the North Indian Ocean.

Prove:

`download → read → QC → harmonize → regrid → align → training sample`

works.

### Phase 4 — Baseline

Train baseline on real data and calculate actual metrics.

### Phase 5 — OceanEmbed

Incrementally add temporal context, missing masks, uncertainty, continuous depth, and regional conditioning.

### Phase 6 — Evaluation

Run standard-depth, arbitrary-depth, regional, missing-data, uncertainty and ablation experiments.

### Phase 7 — ARGO

Run independent ARGO validation.

### Phase 8 — Scientific outputs

Generate actual figures and tables.

### Phase 9 — Backend

Build FastAPI and connect inference.

### Phase 10 — Frontend

Build React dashboard.

### Phase 11 — Integration

Connect:

`Frontend → FastAPI → inference → OceanEmbed → data/model artifacts`

### Phase 12 — Final QA

Run tests, build frontend, test API, test model inference, and perform an end-to-end demonstration.

---

## 30. Autonomous agent behavior

The agent has full implementation ownership.

Do not repeatedly ask the user to:

- create folders;
- create files;
- write code;
- move files;
- manually configure paths.

Create and modify files yourself.

Run commands yourself.

Install reasonable project dependencies where possible.

Run tests.

Inspect errors.

Fix errors.

Iterate.

If a decision is ambiguous, choose the most scientifically defensible and practical option, document it, and continue.

If external credentials/access are required, document the exact blocker and continue with all other work.

---

## 31. Anti-fabrication rule

Never invent:

- data;
- ARGO observations;
- metrics;
- predictions;
- confidence;
- citations;
- URLs;
- scientific conclusions.

If results are unavailable, explicitly write:

`RESULT NOT YET AVAILABLE`

If synthetic data is used, label it:

`DEMO / SYNTHETIC`

---

## 32. Definition of done

The prototype should contain, as far as actual dataset access and hardware permit:

- real-data ingestion;
- official dataset metadata;
- reproducible preprocessing;
- daily 0.25° grid;
- baseline model;
- OceanEmbed model;
- continuous-depth querying;
- uncertainty estimation;
- missing-data handling;
- temporal context;
- regional conditioning;
- thermocline analysis;
- independent ARGO validation;
- quantitative metrics;
- ablation experiments;
- scientific visualizations;
- FastAPI backend;
- React dashboard;
- tests;
- documentation;
- reproducible commands;
- clearly labelled demo mode if required.

---

## 33. FIRST ACTION — START NOW

Immediately inspect the current workspace.

Then actually:

1. initialize the OceanEmbed repository;
2. create all required folders/files;
3. create configuration and documentation;
4. inspect hardware/software;
5. create `data_sources.yaml`;
6. implement the data acquisition framework;
7. verify official dataset access mechanisms;
8. begin a small real-data end-to-end pipeline;
9. run tests;
10. fix errors;
11. continue automatically to the next phase.

Do NOT merely provide instructions.

**Actually build the project in the current workspace.**

After each major phase, report briefly:

- files created/changed;
- commands executed;
- tests run;
- successes;
- failures;
- fixes;
- datasets actually accessible;
- actual model/result status;
- next phase.

# END
