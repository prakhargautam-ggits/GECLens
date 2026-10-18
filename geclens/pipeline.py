"""End-to-end evaluation: score several systems, add intervals and tests, write tables and figures."""
from __future__ import annotations

import json
import os
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from . import report
from .data import build_subsets, reference_stats
from .m2 import read_m2
from .profile import profile_table, ranked_types
from .score import BETA, SystemScore, score_system
from .stats import bootstrap_ci, compare_systems


def score_many(source: str, reference: str, systems: Dict[str, str], selector="R:VERB:SVA",
               cache_dir: Optional[str] = None, tokenise: bool = False, beta: float = BETA,
               verbose: bool = True) -> Dict[str, SystemScore]:
    ref_sents = read_m2(reference)
    subsets = build_subsets(ref_sents, selector)
    out = {}
    for name, path in systems.items():
        if verbose:
            print(f"[geclens] scoring {name}")
        out[name] = score_system(name, source, reference, path, selector, subsets=subsets, cache_dir=cache_dir,
                                 tokenise=tokenise, beta=beta)
    return out


def evaluate(source: str, reference: str, systems: Dict[str, str], selector="R:VERB:SVA", out_dir: str = "geclens_out",
             ci: bool = True, resamples: int = 2000, compare: bool = True,
             measures: Sequence[str] = ("type_only", "overcorrection"), baseline: Optional[str] = None,
             pairs: Optional[Iterable[Tuple[str, str]]] = None, shuffles: int = 10000, seed: int = 13,
             profile: bool = True, profile_group: str = "category", profile_top: int = 12,
             cache_dir: Optional[str] = None, tokenise: bool = False, beta: float = BETA, verbose: bool = True) -> dict:
    """Run the full GECLens evaluation and write results to ``out_dir``.

    Files written: ``subsets.json``, ``reference_stats.json``, ``scores.csv``, ``scores.md``, ``scores.tex``,
    ``<system>.json``, ``comparisons.md``/``.json`` (if ``compare``), ``scatter.png``, and ``profile.png``/``.json``
    (if ``profile``).
    """
    os.makedirs(out_dir, exist_ok=True)
    cache_dir = cache_dir or os.path.join(out_dir, "m2_cache")
    sub = build_subsets(reference, selector)
    sub.to_json(os.path.join(out_dir, "subsets.json"))
    with open(os.path.join(out_dir, "reference_stats.json"), "w", encoding="utf-8") as fh:
        json.dump({**reference_stats(reference), "selector": sub.selector, "subset_sizes": sub.sizes()}, fh, indent=1)

    scores = score_many(source, reference, systems, selector, cache_dir, tokenise, beta, verbose)
    for name, sc in scores.items():
        sc.to_json(os.path.join(out_dir, f"{_safe(name)}.json"))

    cis = None
    if ci and resamples:
        if verbose:
            print("[geclens] bootstrap confidence intervals")
        cis = {n: bootstrap_ci(sc, resamples=resamples, seed=seed, beta=beta) for n, sc in scores.items()}
        with open(os.path.join(out_dir, "confidence_intervals.json"), "w", encoding="utf-8") as fh:
            json.dump(cis, fh, indent=1)

    table = report.rows(scores, cis=cis)
    report.write_csv(os.path.join(out_dir, "scores.csv"), scores)
    with open(os.path.join(out_dir, "scores.md"), "w", encoding="utf-8") as fh:
        fh.write(f"Selector: `{sub.selector}` | positive sentences: {len(sub.positive)} | "
                 f"unedited sentences: {len(sub.unedited)} | total: {sub.n}\n\n")
        fh.write(report.markdown_table(table))
    with open(os.path.join(out_dir, "scores.tex"), "w", encoding="utf-8") as fh:
        fh.write(report.latex_table(table, caption=f"GECLens results for {sub.selector}"))

    result = {"selector": sub.selector, "subsets": sub.sizes(), "scores": {n: s.summary() for n, s in scores.items()}}
    if compare and len(scores) > 1:
        if verbose:
            print("[geclens] paired approximate randomisation tests")
        comps = compare_systems(scores, measures, pairs=pairs, baseline=baseline, shuffles=shuffles,
                                resamples=resamples, seed=seed, beta=beta)
        with open(os.path.join(out_dir, "comparisons.md"), "w", encoding="utf-8") as fh:
            fh.write(report.comparisons_markdown(comps))
        with open(os.path.join(out_dir, "comparisons.json"), "w", encoding="utf-8") as fh:
            json.dump([c.as_dict() for c in comps], fh, indent=1)
        result["comparisons"] = [c.as_dict() for c in comps]

    report.scatter_plot(scores, os.path.join(out_dir, "scatter.png"), title=f"{sub.selector}")
    if profile:
        types = ranked_types(reference, profile_group, profile_top)
        prof = profile_table(scores, group=profile_group, types=types)
        prof = {t: prof[t] for t in types if t in prof}
        with open(os.path.join(out_dir, "profile.json"), "w", encoding="utf-8") as fh:
            json.dump(prof, fh, indent=1)
        report.heatmap(prof, os.path.join(out_dir, "profile.png"), systems=list(scores))
        result["profile_types"] = list(prof)
    if verbose:
        print(f"[geclens] results written to {out_dir}")
    return result


def _safe(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in name)
