"""YAML configuration runner: one file describes data, systems, error types and statistics.

Example::

    source: data/src.txt
    reference: data/ref.m2
    out_dir: results
    selectors: [R:VERB:SVA, DET, PREP]      # one evaluation per selector
    systems:
      baseline: outputs/baseline.txt
      improved: outputs/improved.txt
    statistics:
      bootstrap_resamples: 2000
      shuffles: 10000
      measures: [type_only, overcorrection]
      baseline: baseline
      seed: 13
    profile: {group: category, top: 12}

Relative paths are resolved against the directory of the configuration file.
"""
from __future__ import annotations

import os

import yaml

from .pipeline import evaluate


def run_config(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    base = os.path.dirname(os.path.abspath(path))
    res = lambda p: p if os.path.isabs(p) else os.path.join(base, p)
    selectors = cfg.get("selectors") or [cfg.get("selector", "R:VERB:SVA")]
    stats = cfg.get("statistics", {}) or {}
    prof = cfg.get("profile", {}) or {}
    out_root = res(cfg.get("out_dir", "geclens_out"))
    systems = {k: res(v) for k, v in cfg["systems"].items()}
    results = {}
    for i, sel in enumerate(selectors):
        sub = out_root if len(selectors) == 1 else os.path.join(out_root, sel.replace(":", "_").replace(",", "+").replace("*", "x"))
        results[sel] = evaluate(
            res(cfg["source"]), res(cfg["reference"]), systems, selector=sel, out_dir=sub,
            ci=stats.get("bootstrap_resamples", 2000) > 0, resamples=stats.get("bootstrap_resamples", 2000),
            compare=stats.get("compare", True), measures=stats.get("measures", ["type_only", "overcorrection"]),
            baseline=stats.get("baseline"), shuffles=stats.get("shuffles", 10000), seed=stats.get("seed", 13),
            profile=prof.get("enabled", True) and i == 0, profile_group=prof.get("group", "category"),
            profile_top=prof.get("top", 12), cache_dir=os.path.join(out_root, "m2_cache"),
            tokenise=cfg.get("tokenise", False))
    return results
