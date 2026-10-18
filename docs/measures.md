# What GECLens measures

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

## Statistics

- **Bootstrap confidence intervals**: sentences are resampled with replacement (B resamples, seeded); each measure is recomputed from the summed per-sentence components; the 2.5th and 97.5th percentiles give the unadjusted 95% interval.
- **Paired approximate randomisation**: for each shuffle, the outputs of the two systems are swapped sentence by sentence with probability 0.5; the two-sided p-value is (number of shuffles with |d*| >= |d|, plus one) / (shuffles + 1).
- **Paired bootstrap interval of a difference**: both systems are resampled with the same sentence indices.
- **Holm–Bonferroni**: all tests run in one `compare` call form one family.
