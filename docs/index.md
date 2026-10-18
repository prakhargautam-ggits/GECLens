# GECLens

**Error-type-targeted evaluation of grammatical error correction (GEC) systems.**

[![tests](https://github.com/prakhargautam-ggits/GECLens/actions/workflows/ci.yml/badge.svg)](https://github.com/prakhargautam-ggits/GECLens/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.9%E2%80%933.12-blue) ![license](https://img.shields.io/badge/license-MIT-green)

Overall F0.5 hides how a system handles a single kind of error. Subject–verb agreement, articles, prepositions and tense
each make up only a few per cent of all edits. GECLens answers two questions for any ERRANT error type:

1. **Does the system fix these errors?** Type F0.5, type-only F0.5, sentence-level detection and correction success.
2. **What does it break while trying?** Over-correction on sentences the references leave unchanged.

Every measure comes with bootstrap confidence intervals and paired significance tests (approximate randomisation with
Holm correction), for any number of systems. Results are written as CSV, Markdown and LaTeX tables and as figures.

GECLens builds on [ERRANT](https://github.com/chrisjbryant/errant) for alignment and edit typing. Its edit-level scores
are **identical** to `errant_compare`. This is checked in the test suite.


## Installation

```bash
pip install geclens            # or, from source: pip install -e .
python -m spacy download en_core_web_sm
```

Requirements: Python 3.9–3.12, ERRANT 3.0.2, spaCy 3.4–3.7 with `en_core_web_sm`, NumPy, Matplotlib and PyYAML. GECLens
runs on Linux, macOS and Windows.

## Quick start

```bash
cd examples/toy
geclens run config.yaml          # about 5 seconds
```

This scores three toy systems on 30 sentences for three error types and writes `results/`. The toy data were written by
the GECLens authors and are released under CC0.

| System | Overall F0.5 | Type F0.5 | Type-only F0.5 | Detection F1 | Success | Over-corr. |
|---|---|---|---|---|---|---|
| careful | 0.882 | 0.972 | 0.972 | 0.933 | 87.5% | 0.0% |
| eager | 0.649 | 0.987 | 0.987 | 0.968 | 93.8% | 100.0% |
| cautious | 0.312 | 0.435 | 0.435 | 0.222 | 12.5% | 0.0% |

*eager* fixes agreement errors as well as *careful*, but it also rewrites every correct sentence. Type-level F0.5 alone
would not show this.

## Correctness

- Overall and per-type TP/FP/FN equal `errant_compare -cat 3` (see `tests/test_score.py`).
- Statistical routines are tested on known cases: identical systems give p = 1, Holm values are checked by hand, and
  bootstrap intervals contain the point estimate.
- The CI runs the suite on Python 3.9–3.12.

```bash
pip install -e ".[dev]" && pytest
```

## Citation

If you use GECLens, please cite the software (see `CITATION.cff`):

> P. Gautam, J. S. Thakur, A. Mishra. *GECLens: A Python toolkit for error-type-targeted evaluation of grammatical error
> correction systems.* Version 1.0.0, 2026. https://github.com/prakhargautam-ggits/GECLens
