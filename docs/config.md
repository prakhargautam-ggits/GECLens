# Configuration file

```yaml
source: src.txt
reference: ref.m2
out_dir: results
selectors: [R:VERB:SVA, PREP, DET]      # one evaluation per selector
systems: {careful: careful.txt, eager: eager.txt, cautious: cautious.txt}
statistics: {bootstrap_resamples: 2000, shuffles: 10000, measures: [type_only, overcorrection], baseline: cautious, seed: 13}
profile: {group: category, top: 12}
```

Relative paths are resolved against the folder of the configuration file. With several selectors, each gets its own sub-folder of `out_dir`.
