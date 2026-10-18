# Command line

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
