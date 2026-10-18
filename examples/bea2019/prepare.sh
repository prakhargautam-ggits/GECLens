#!/usr/bin/env bash
# Fetch the released system outputs of Omelianchuk et al. (BEA 2024) and extract the BEA-2019 dev source sentences.
set -e
[ -d pillars-of-gec ] || git clone --depth 1 https://github.com/grammarly/pillars-of-gec
grep '^S ' pillars-of-gec/data/evaluation_sets/bea-dev.m2 | cut -c3- > src.txt
echo "Ready: run 'geclens run config.yaml'"
