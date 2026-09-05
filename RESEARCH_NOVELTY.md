# OceanEmbed — Research Novelty

## Positioning Statement

Generic satellite-based subsurface ocean temperature reconstruction is an
established research area. We do NOT claim this as novel.

We do NOT claim:
- "first ever" system
- "world's first" approach
- superiority over prior work without experimental evidence
- guaranteed performance improvements

## Claimed Contribution

OceanEmbed contributes an **integrated combination** of:

1. **Continuous-Depth Querying** — Unlike systems that predict only at fixed depth levels,
   OceanEmbed accepts arbitrary depth queries between 0 and 1000 m via a Fourier-encoded
   continuous decoder. This enables interpolation at non-standard depths and is evaluated
   against arbitrary-depth ARGO observations.

2. **Explicit Uncertainty Estimation** — Heteroscedastic regression provides a
   per-prediction uncertainty estimate. This distinguishes confident predictions in
   data-rich regions from uncertain predictions under data scarcity.

3. **Missing-Data Resilience** — Explicit binary validity masks per input channel allow
   the model to adapt gracefully to missing satellite observations (e.g., cloud-obscured
   SST). The hypothesis that useful predictions can be maintained under missing inputs is
   experimentally tested.

4. **North Indian Ocean Focus** — The model is specifically designed, trained, and
   validated for the North Indian Ocean (5–30°N, 45–105°E), including distinct treatment
   of the Bay of Bengal and Arabian Sea.

5. **Independent ARGO Validation** — Performance is evaluated against in-situ ARGO
   float profiles that are kept completely separate from training data, providing a
   scientifically rigorous validation protocol.

6. **Interactive Scientific Inference** — A React dashboard enables scientists and
   decision-makers to query the model at arbitrary locations, depths, and dates, and to
   interactively demonstrate missing-data robustness.

## Related Work

The coordinate-conditioned neural representation design is conceptually inspired by
neural radiance fields and implicit neural representations, but applied to a very
different domain (ocean reconstruction from satellite inputs, not scene rendering).
We do not call this system "NeRF" or claim NeRF as our contribution.

Prior satellite-to-subsurface reconstruction systems include:
- Su et al. (2015, 2021): Argo-satellite regression approaches
- Maturi et al. (2020): operational SST-based thermocline depth prediction
- Various deep learning papers on subsurface reconstruction

OceanEmbed differs in the integrated combination of continuous depth, uncertainty,
and missing-data handling, demonstrated specifically for the North Indian Ocean.

## Hypothesis

**H1**: A CNN encoder with continuous depth decoder learns useful subsurface
temperature representations from surface observations (testable vs. GLORYS12V1 RMSE).

**H2**: Explicit missing-data masks maintain prediction quality under partial input
availability, at the cost of increased uncertainty (testable via missing-data experiments).

**H3**: Heteroscedastic uncertainty correlates with actual prediction error,
providing meaningful confidence calibration (testable via calibration evaluation).

**H4**: Regional conditioning improves regional performance beyond the shared-backbone
baseline (testable via ablation study).

All hypotheses are tested experimentally and reported only if results are available.
