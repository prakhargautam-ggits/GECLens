# Changelog

## 1.0.2 (2026-11-10)

Maintenance release; scores and outputs are unchanged.
- Installation fix: `thinc>=8.2.5,<8.3` is now required. A fresh `pip install geclens` could pick an older thinc
  build together with NumPy 2.x, which fails on import with "numpy.dtype size changed".
- `requires-python` is now `>=3.9,<3.13`, matching the tested versions (spaCy 3.7 has no Python 3.13 wheels).
- Package metadata lists all three authors.

## 1.0.1 (2026-10-18)

- `tokenise` option: only the system outputs are tokenised; the source keeps the tokens of the reference M2.
  Plain-text outputs (for example from a chat model) can now be scored directly.
- Toy example: contractions are tokenised as in standard GEC data ("do n't"); the toy table changes slightly.
- `scripts/check_against_errant.py` also checks per-sentence counts against ERRANT's chosen annotator.
- Tests on Linux, macOS and Windows.

## v1.0.0 (2026-10)
First public release.
- Type-targeted subsets for any ERRANT edit type, category, pattern or list.
- Scoring: overall, type and type-only P/R/F0.5 (identical to `errant_compare`), sentence-level detection, correction
  success, over-correction on unedited sentences, change rate.
- Statistics: percentile bootstrap CIs, paired approximate randomisation, paired bootstrap CIs of differences, Holm.
- Error-type profiles (system x type heatmap), CSV/Markdown/LaTeX tables, scatter plot.
- CLI (`subset`, `score`, `compare`, `profile`, `run`) and YAML configuration runner.
