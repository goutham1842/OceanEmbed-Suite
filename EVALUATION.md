# OceanEmbed — Evaluation Methodology

## Metrics

| Metric | Formula | Computed at |
|---|---|---|
| RMSE | √(mean(T_pred - T_obs)²) | All SIH depths, arbitrary depths |
| MAE | mean(|T_pred - T_obs|) | All depths |
| Bias | mean(T_pred - T_obs) | All depths |
| Pearson r | Pearson correlation | All depths |
| R² | 1 - SS_res/SS_tot | Depth-wise |
| Thermocline depth error | |z_thermo_pred - z_thermo_ref| | Per profile |

## Evaluation Dimensions

- **SIH standard depths**: 0, 5, 10, 20, 30, 50, 75, 100, 125, 150, 200, 300, 500, 700, 1000 m
- **Arbitrary depths**: any depth in [0, 1000] m
- **Depth bands**: 0–100, 100–300, 300–500, 500–700, 700–1000 m
- **Regional**: Arabian Sea vs Bay of Bengal
- **Temporal**: monthly, seasonal patterns
- **Uncertainty calibration**: predicted σ² vs actual error²

## Evaluation Data

- **Validation set**: GLORYS12V1, 2019–2020 (chronologically held out)
- **Test set**: GLORYS12V1, 2021–2022 (chronologically held out)
- **Independent validation**: INCOIS/GDAC ARGO profiles (never seen during training)

## RESULT NOT YET AVAILABLE

All evaluation metrics require trained model and real data.
See ROADMAP.md for blockers.

When results become available, they will be stored in:
- `artifacts/metrics/baseline_metrics.json`
- `artifacts/metrics/ocean_embed_metrics.json`
- `artifacts/metrics/argo_validation_metrics.json`
- `artifacts/metrics/ablation_study.json`
