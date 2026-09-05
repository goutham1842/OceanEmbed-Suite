# OceanEmbed — Roadmap

## Current Status

- ✅ Phase 1: Environment inspection, repository structure, configuration, documentation
- ✅ Phase 2: Data framework (download scripts, preprocessing pipeline, harmonization)
- ✅ Phase 3: Small real-data slice pipeline (requires credentials — see BLOCKERS)
- ✅ Phase 4: Baseline model implementation (V1)
- ✅ Phase 5: OceanEmbed full model (V2–V7)
- ✅ Phase 6: Evaluation framework
- ✅ Phase 7: ARGO validation pipeline
- ✅ Phase 8: Scientific outputs framework
- ✅ Phase 9: FastAPI backend
- ✅ Phase 10: React/Vite frontend
- ✅ Phase 11: Integration
- 🔲 Phase 3 (execution): Real data download (BLOCKED — credentials required)
- 🔲 Phase 4 (execution): Real baseline training (BLOCKED — data required)
- 🔲 Phase 6 (execution): Real metrics computation (BLOCKED — model required)
- 🔲 Phase 7 (execution): Real ARGO validation (BLOCKED — data required)

## Blockers

### BLOCKER 1: CMEMS Credentials
**Required for**: GLORYS12V1, OSTIA SST, CMEMS SSS, DUACS SLA  
**Action**: Register at https://marine.copernicus.eu/, add credentials to `.env`

### BLOCKER 2: CDS API Key
**Required for**: ERA5 surface winds  
**Action**: Register at https://cds.climate.copernicus.eu/, add key to `.env`

### BLOCKER 3: GPU for Practical Training
**Current**: CPU-only (12 cores, no CUDA)  
**Action**: Run on GPU-equipped server or Google Colab/cloud instance

## Next Steps (after credentials available)

1. Run `python scripts/download/download_glorys.py --test-slice` to verify CMEMS access
2. Run full preprocessing pipeline
3. Train baseline model (V1) with real data
4. Compute actual RMSE/MAE metrics
5. Incrementally add model components (V2–V7)
6. Run ARGO validation
7. Generate scientific figures
8. Switch frontend/backend from DEMO to REAL mode

## Future Enhancements

- Longer temporal context (7 days, monthly climatology)
- Ensemble uncertainty (MC Dropout or deep ensembles)
- 3D spatial attention
- Operational INCOIS integration
- Real-time satellite ingestion pipeline
- Transformer-based encoder for global context
