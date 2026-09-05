# OceanEmbed — Implementation Plan

## Environment Summary
- **OS**: Windows 10 (Build 26200)
- **Python**: 3.13.1
- **Node**: v22.13.1 / npm 11.1.0
- **Git**: 2.46.0
- **CPU**: 12 cores
- **GPU**: None (CPU-only PyTorch 2.8.0)
- **Disk**: 511 GB total, 245 GB free
- **Key libs**: PyTorch 2.8.0+cpu, NumPy 2.3.3, xarray 2026.7.0

## Strategy (CPU-only)
- Use small CPU-friendly configs (batch=4, tiny model) for training
- Demo mode clearly labelled for UI/software when real model not trained yet
- Install all missing Python dependencies via pip
- Use Copernicus Marine Toolbox for data access (requires credentials - will document)

## Phase Execution Order
1. ✅ Environment inspect (done)
2. Repository + folder structure + .gitignore + configs
3. Documentation (all .md files)
4. data_sources.yaml + DATA_SOURCES.md
5. Python requirements.txt + install
6. Data download framework (scripts/download/)
7. Preprocessing/harmonization pipeline (src/data/)
8. Baseline model (src/models/baseline.py)
9. OceanEmbed model (src/models/ocean_embed.py)
10. Training scripts
11. Evaluation framework
12. ARGO validation pipeline
13. FastAPI backend
14. React/Vite frontend
15. Tests
16. Integration + QA

## Open Questions (resolved by spec)
- Continuous depth: Fourier positional encoding on normalized depth
- Uncertainty: heteroscedastic regression (mean + log variance)
- Regional conditioning: shared backbone + region embedding token
- ARGO: separate from training data; query model at ARGO depths
