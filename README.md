# OceanEmbed

**Continuous, Uncertainty-Aware and Missing-Data-Resilient Subsurface Ocean Temperature Reconstruction**

**Smart India Hackathon 2026 | SIH26066**  
**Organization:** Ministry of Earth Sciences / INCOIS  
**Domain:** Software / Space Technology

---

## Objective

OceanEmbed reconstructs the 3D subsurface temperature field of the North Indian Ocean
from surface satellite observations. The system accepts daily satellite observations
(SST, SSS, SSH, surface currents, surface winds) and predicts temperature at
**arbitrary depths from 0 to 1000 m** over the domain:

| Dimension | Range |
|---|---|
| Latitude | 5°N – 30°N |
| Longitude | 45°E – 105°E |
| Spatial grid | 0.25° × 0.25° |
| Temporal | Daily |
| Depth | 0 – 1000 m (continuous) |

---

## Research Hypothesis

> Learning a continuous latent representation of the hidden ocean state from
> multimodal surface observations enables scientifically useful subsurface
> temperature predictions, where explicitly modelling uncertainty and data gaps
> produces more reliable outputs than single-point predictions.

This is a testable hypothesis, not a guaranteed result. All claims are backed by
measured metrics against GLORYS12V1 targets and independent ARGO validation.

---

## Core Contributions

1. **Continuous Depth-Conditioned Ocean Representation** — query temperature at any depth 0–1000 m, not only fixed levels
2. **Explicit Missingness Masks** — handles missing satellite observations gracefully
3. **Uncertainty Estimation** — heteroscedastic regression returns prediction confidence
4. **Temporal Context** — uses a 3-day sliding window (t-2, t-1, t)
5. **Region-Aware Learning** — shared backbone with Bay of Bengal / Arabian Sea conditioning
6. **Thermocline Analysis** — detects and evaluates thermocline depth
7. **Independent ARGO Validation** — evaluated against in-situ floats

---

## Quick Start

```bash
# 1. Clone repository
git clone <repo_url>
cd OceanEmbed

# 2. Create environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure credentials
cp .env.example .env
# Edit .env with your CMEMS credentials (see DATA_SOURCES.md)

# 5. Run pipeline (small test slice)
python scripts/download/download_glorys.py --test-slice
python scripts/preprocess/harmonize.py --config configs/data_config.yaml
python scripts/train/train_baseline.py --config configs/training_config.yaml

# 6. Start backend
cd backend
uvicorn main:app --reload

# 7. Start frontend
cd frontend
npm install
npm run dev
```

---

## Project Structure

```
OceanEmbed/
├── README.md                  ← this file
├── ARCHITECTURE.md            ← model architecture
├── DATA_SOURCES.md            ← dataset documentation
├── MODEL.md                   ← detailed model description
├── TRAINING.md                ← training procedures
├── EVALUATION.md              ← evaluation methodology
├── ARGO_VALIDATION.md         ← ARGO validation protocol
├── DEMO.md                    ← demo mode documentation
├── LIMITATIONS.md             ← known limitations
├── RESEARCH_NOVELTY.md        ← novelty positioning
├── ROADMAP.md                 ← development roadmap
├── data_sources.yaml          ← machine-readable dataset registry
├── requirements.txt
├── .env.example
├── .gitignore
├── configs/
│   ├── config.yaml            ← global config
│   ├── data_config.yaml       ← data/split/preprocessing config
│   ├── model_config.yaml      ← model architecture config
│   └── training_config.yaml   ← training hyperparameters
├── data/
│   ├── raw/                   ← raw downloaded data (not committed)
│   ├── interim/               ← harmonized/regridded data
│   └── processed/             ← train/val/test samples
├── scripts/
│   ├── download/              ← data acquisition scripts
│   ├── preprocess/            ← preprocessing pipeline
│   ├── train/                 ← training runners
│   └── evaluate/              ← evaluation scripts
├── src/
│   ├── data/                  ← dataset classes, transforms
│   ├── models/                ← all model implementations
│   ├── training/              ← trainer, losses, metrics
│   ├── evaluation/            ← evaluation pipeline
│   └── inference/             ← inference engine
├── backend/                   ← FastAPI REST API
├── frontend/                  ← React/Vite dashboard
├── notebooks/                 ← exploration notebooks
├── tests/                     ← pytest test suite
└── artifacts/
    ├── figures/               ← generated plots
    ├── metrics/               ← JSON metrics files
    └── checkpoints/           ← model checkpoints
```

---

## Dataset Access

Data access requires Copernicus Marine Service (CMEMS) credentials.
See [DATA_SOURCES.md](DATA_SOURCES.md) and [`.env.example`](.env.example).

| Dataset | Status | Notes |
|---|---|---|
| GLORYS12V1 | Requires CMEMS credentials | Primary training target |
| OSTIA SST | Requires CMEMS credentials | Primary SST input |
| DUACS SLA | Requires CMEMS credentials | SSH + geostrophic currents |
| CMEMS SSS | Requires CMEMS credentials | Primary SSS input |
| ERA5 Winds | Requires CDS API key | Surface winds |
| INCOIS ARGO | Public access | Independent validation |

---

## Demo Mode

Until real data and model training are complete, the backend serves clearly labelled
`DEMO / SYNTHETIC` outputs for software/UI testing. See [DEMO.md](DEMO.md).

**Synthetic outputs are never presented as scientific results.**

---

## Novelty Statement

See [RESEARCH_NOVELTY.md](RESEARCH_NOVELTY.md) for scientifically defensible
novelty positioning. Generic satellite-to-subsurface reconstruction is not claimed
as novel. The contribution is the **integrated combination** of continuous-depth
querying, explicit uncertainty, missing-data resilience, regional conditioning,
and independent ARGO validation.

---

## License

To be determined by INCOIS / Ministry of Earth Sciences guidelines.

---

## Citation

> K Satya Sai Sailesh et al. *OceanEmbed: Continuous, Uncertainty-Aware and
> Missing-Data-Resilient Subsurface Ocean Temperature Reconstruction.*
> Smart India Hackathon 2026, SIH26066.
