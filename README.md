# GECLens

**Error-type-targeted evaluation of grammatical error correction (GEC) systems.**

[![tests](https://github.com/prakhargautam-ggits/GECLens/actions/workflows/ci.yml/badge.svg)](https://github.com/prakhargautam-ggits/GECLens/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/geclens)](https://pypi.org/project/geclens/) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23449073.svg)](https://doi.org/10.5281/zenodo.23449073) ![python](https://img.shields.io/badge/python-3.9%E2%80%933.12-blue) ![license](https://img.shields.io/badge/license-MIT-green)

Overall F0.5 hides how a system handles a single kind of error. Subject–verb agreement, articles, prepositions and tense
each make up only a few per cent of all edits. GECLens answers two questions for any ERRANT error type:

1. **Does the system fix these errors?** Type F0.5, type-only F0.5, sentence-level detection and correction success.
2. **What does it break while trying?** Over-correction on sentences the references leave unchanged.

Every measure comes with bootstrap confidence intervals and paired significance tests (approximate randomisation with
Holm correction), for any number of systems. Results are written as CSV, Markdown and LaTeX tables and as figures.

GECLens builds on [ERRANT](https://github.com/chrisjbryant/errant) for alignment and edit typing. Its edit-level scores
are **identical** to `errant_compare`. This is checked in the test suite.

---

## Installation

```bash
pip install geclens            # or, from source: pip install -e .
python -m spacy download en_core_web_sm
```

Requirements: Python 3.9–3.12, ERRANT 3.0.2, spaCy 3.4–3.7 with `en_core_web_sm`, NumPy, Matplotlib and PyYAML. GECLens
runs on Linux, macOS and Windows.

## Quick start (toy data included)

```bash
cd examples/toy
geclens run config.yaml          # about 5 seconds
```

This scores three toy systems on 30 sentences for three error types and writes `results/`. The toy data were written by
the GECLens authors and are released under CC0.

| System | Overall F0.5 | Type F0.5 | Type-only F0.5 | Detection F1 | Success | Over-corr. |
|---|---|---|---|---|---|---|
| careful | 0.882 | 0.974 | 0.974 | 0.938 | 88.2% | 0.0% |
| eager | 0.649 | 0.988 | 0.988 | 0.970 | 94.1% | 100.0% |
| cautious | 0.312 | 0.417 | 0.417 | 0.211 | 11.8% | 0.0% |

*eager* fixes agreement errors as well as *careful*, but it also rewrites every correct sentence. Type-level F0.5 alone
would not show this.

## What GECLens measures

For an error-type selector **T** (for example `R:VERB:SVA`):

| Measure | Definition |
|---|---|
| `overall` | ERRANT precision, recall and F0.5 over all edits |
| `type` | ERRANT P/R/F0.5 for edits of type T, for the annotator ERRANT selects per sentence (the one that maximises overall F0.5) |
| `type_only` | P/R/F0.5 after restricting hypothesis **and** reference edits to T, so the annotator choice depends on T edits only. Use it to compare systems that make different amounts of other edits. |
| `detection` | Sentence-level P/R/F1 for "the sentence contains a T error" |
| `success` | Share of T-positive sentences where every T edit of at least one annotator was produced exactly |
| `overcorrection` | Share of **unedited** reference sentences that the system changed (whitespace and quote style ignored) |
| `change_rate` | Share of all sentences the system changed |

**Subsets** (`geclens subset`): `positive` (some annotator made a T edit), `positive_all`, `unedited` (no annotator made
any edit), `unedited_any`, and `other`.

**Error-type selectors:**
- an exact type (`R:VERB:SVA`);
- a category, which matches its M/R/U variants (`DET`);
- a pattern (`R:VERB*`);
- a comma-separated list (`PREP,DET`).

## Command line

```bash
# subsets and reference statistics
geclens subset  --ref ref.m2 --type R:VERB:SVA --out subsets.json

# scores with 95% bootstrap confidence intervals
geclens score   --src src.txt --ref ref.m2 --type DET \
                --hyp sysA=a.txt sysB=b.txt --ci 2000 --out-dir results

# paired approximate randomisation, Holm-adjusted, every system vs a baseline
geclens compare --src src.txt --ref ref.m2 --type PREP --hyp sysA=a.txt sysB=b.txt base=c.txt \
                --baseline base --measures type_only overcorrection --shuffles 10000

# system x error-type heatmap of ERRANT F0.5
geclens profile --src src.txt --ref ref.m2 --hyp a.txt b.txt c.txt --group category --top 12

# everything from one configuration file
geclens run config.yaml
```

Inputs:
- `--src`: tokenised source sentences, one per line.
- `--ref`: an ERRANT-typed reference M2 file. If you only have corrected text, create it with
  `errant_parallel -orig src.txt -cor ref1.txt [ref2.txt ...] -out ref.m2`.
- `--hyp`: system outputs as text (one sentence per line) or as ready-made `.m2` files.

Hypothesis M2 files are built once with ERRANT and cached.

## Python API

```python
from geclens import score_many, bootstrap_ci, compare_systems, profile_table, evaluate

scores = score_many("src.txt", "ref.m2", {"A": "a.txt", "B": "b.txt"}, selector="R:VERB:SVA")
scores["A"].metrics["type_only"]                    # {'tp':…, 'fp':…, 'fn':…, 'P':…, 'R':…, 'F0.5':…}
bootstrap_ci(scores["A"], resamples=2000)           # {'overall': (lo, hi), 'type': …, …}
compare_systems(scores, ["type_only", "overcorrection"], baseline="B")

evaluate("src.txt", "ref.m2", {"A": "a.txt", "B": "b.txt"}, selector="PREP", out_dir="results")
```

## Configuration file

```yaml
source: src.txt
reference: ref.m2
out_dir: results
selectors: [R:VERB:SVA, PREP, DET]      # one evaluation per selector
systems: {careful: careful.txt, eager: eager.txt, cautious: cautious.txt}
statistics: {bootstrap_resamples: 2000, shuffles: 10000, measures: [type_only, overcorrection], baseline: cautious, seed: 13}
profile: {group: category, top: 12}
```

## Output files

| File | Content |
|---|---|
| `scores.csv` / `.md` / `.tex` | One row per system; the Markdown and LaTeX tables include 95% CIs |
| `<system>.json` | All measures and per-type ERRANT counts |
| `confidence_intervals.json` | Bootstrap intervals |
| `comparisons.md` / `.json` | Differences, paired-bootstrap CIs, p-values and Holm-adjusted p-values |
| `scatter.png` | Type-only F0.5 against over-correction |
| `profile.png` / `.json` | System × error-type heatmap |
| `subsets.json`, `reference_stats.json` | Subset indices and reference statistics |

## Correctness

- Hypothesis M2 files are byte-identical to `errant_parallel`, overall and per-type TP/FP/FN equal
  `errant_compare -cat 3`, and the per-sentence counts equal those of the annotator that `errant_compare -v` reports
  as chosen for each sentence (see `tests/test_score.py`
  and `tests/test_edge_cases.py`). Check this on your own data with
  `python scripts/check_against_errant.py src.txt ref.m2 sys1.txt [sys2.txt ...]`.
- A hand-built case with two annotators covers missed, unnecessary and replacement edits, two target edits in one
  sentence, an unedited sentence and an empty subset; expected values were worked out by hand.
- Statistical routines are tested on known cases: identical systems give p = 1, Holm values are checked by hand, and
  bootstrap intervals contain the point estimate.
- The CI runs the suite on Python 3.9–3.12.

```bash
pip install -e ".[dev]" && pytest
```

## Citation

If you use GECLens, please cite the software (see `CITATION.cff`):

> P. Gautam, J. S. Thakur, A. Mishra. *GECLens: A Python toolkit for error-type-targeted evaluation of grammatical error
> correction systems.* Version 1.0.1, 2026. https://doi.org/10.5281/zenodo.23449073

## Licence and support

- MIT licence (`LICENSE`, `Licence.txt`).
- Questions and bug reports: [GitHub issues](https://github.com/prakhargautam-ggits/GECLens/issues) or
  prakhargautam@jecjabalpur.ac.in.
