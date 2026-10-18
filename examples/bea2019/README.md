# BEA-2019 dev case study

This folder repeats the case study in Section 3.2 of the GECLens paper: nine released GEC systems, scored on
article/determiner (DET), preposition (PREP) and verb tense (VERB:TENSE) errors of the BEA-2019 development set.

```bash
./prepare.sh              # clones grammarly/pillars-of-gec and writes src.txt
geclens run config.yaml   # about 6.5 minutes on one CPU core, including ERRANT alignment
```

The reference file and system outputs are not redistributed here. They come from the
[pillars-of-gec](https://github.com/grammarly/pillars-of-gec) repository (Omelianchuk et al., BEA 2024); the BEA-2019
data are subject to the terms of the shared task (Bryant et al., BEA 2019).
