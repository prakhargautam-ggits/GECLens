# Python API

```python
from geclens import score_many, bootstrap_ci, compare_systems, profile_table, evaluate

scores = score_many("src.txt", "ref.m2", {"A": "a.txt", "B": "b.txt"}, selector="R:VERB:SVA")
scores["A"].metrics["type_only"]                    # {'tp':…, 'fp':…, 'fn':…, 'P':…, 'R':…, 'F0.5':…}
bootstrap_ci(scores["A"], resamples=2000)           # {'overall': (lo, hi), 'type': …, …}
compare_systems(scores, ["type_only", "overcorrection"], baseline="B")

evaluate("src.txt", "ref.m2", {"A": "a.txt", "B": "b.txt"}, selector="PREP", out_dir="results")
```

Main objects: `TypeSelector`, `Subsets` and `build_subsets`, `SystemScore` and `score_system` (`.metrics`, `.components`, `.per_type`), and `bootstrap_ci`, `approx_randomisation`, `paired_bootstrap_ci`, `holm`, `compare_systems`, `profile_table`, `evaluate`.
