# Changelog

## v1.0.0 (2026-10)
First public release.
- Type-targeted subsets for any ERRANT edit type, category, pattern or list.
- Scoring: overall, type and type-only P/R/F0.5 (identical to `errant_compare`), sentence-level detection, correction
  success, over-correction on unedited sentences, change rate.
- Statistics: percentile bootstrap CIs, paired approximate randomisation, paired bootstrap CIs of differences, Holm.
- Error-type profiles (system x type heatmap), CSV/Markdown/LaTeX tables, scatter plot.
- CLI (`subset`, `score`, `compare`, `profile`, `run`) and YAML configuration runner.
