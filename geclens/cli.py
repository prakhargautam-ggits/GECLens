"""Command-line interface: ``geclens subset | score | compare | profile | run``."""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List

from . import __version__, report
from .data import build_subsets, reference_stats


def _systems(items: List[str]) -> Dict[str, str]:
    out = {}
    for it in items:
        if "=" in it:
            name, path = it.split("=", 1)
        else:
            path = it
            name = os.path.splitext(os.path.basename(path))[0]
        if name in out:
            raise SystemExit(f"duplicate system name: {name}")
        out[name] = path
    return out


def _common(p: argparse.ArgumentParser, hyp: bool = True) -> None:
    p.add_argument("--src", required=hyp, help="tokenised source sentences, one per line")
    p.add_argument("--ref", required=True, help="reference M2 file (ERRANT edit types)")
    if hyp:
        p.add_argument("--hyp", nargs="+", required=True, metavar="NAME=PATH",
                       help="system outputs (text, one sentence per line, or .m2); NAME= is optional")
    p.add_argument("--type", default="R:VERB:SVA", help="error-type selector, e.g. R:VERB:SVA, DET, 'R:VERB*', 'PREP,DET'")
    p.add_argument("--tokenise", action="store_true", help="system outputs are plain text: tokenise them with spaCy (the source must already match the reference M2)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="geclens", description="Error-type-targeted evaluation of GEC systems.")
    ap.add_argument("--version", action="version", version=f"geclens {__version__}")
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("subset", help="build type-targeted subsets and reference statistics")
    _common(p, hyp=False)
    p.add_argument("--out", default="subsets.json")

    p = sp.add_parser("score", help="score systems (point estimates and optional bootstrap CIs)")
    _common(p)
    p.add_argument("--out-dir", default="geclens_out")
    p.add_argument("--ci", type=int, default=0, metavar="B", help="bootstrap resamples for 95%% CIs (0 = off)")
    p.add_argument("--seed", type=int, default=13)

    p = sp.add_parser("compare", help="paired significance tests between systems (Holm-adjusted)")
    _common(p)
    p.add_argument("--measures", nargs="+", default=["type_only", "overcorrection"],
                   choices=["overall", "type", "type_only", "detection", "success", "overcorrection", "change_rate"])
    p.add_argument("--baseline", help="compare every system with this one (default: all pairs)")
    p.add_argument("--shuffles", type=int, default=10000)
    p.add_argument("--resamples", type=int, default=2000, help="paired bootstrap resamples for CIs of differences")
    p.add_argument("--seed", type=int, default=13)
    p.add_argument("--out-dir", default="geclens_out")

    p = sp.add_parser("profile", help="system x error-type heatmap of ERRANT F0.5")
    _common(p)
    p.add_argument("--group", choices=["type", "category"], default="category")
    p.add_argument("--top", type=int, default=12, help="most frequent reference types/categories to show")
    p.add_argument("--out-dir", default="geclens_out")

    p = sp.add_parser("run", help="run a full evaluation from a YAML configuration file")
    p.add_argument("config")

    a = ap.parse_args(argv)

    if a.cmd == "subset":
        sub = build_subsets(a.ref, a.type)
        sub.to_json(a.out)
        print(json.dumps({**sub.sizes(), "selector": sub.selector}, indent=1))
        return 0

    if a.cmd == "run":
        from .config import run_config
        run_config(a.config)
        return 0

    from .pipeline import score_many
    systems = _systems(a.hyp)
    os.makedirs(a.out_dir, exist_ok=True)
    scores = score_many(a.src, a.ref, systems, a.type, os.path.join(a.out_dir, "m2_cache"), a.tokenise)

    if a.cmd == "score":
        cis = None
        if a.ci:
            from .stats import bootstrap_ci
            cis = {n: bootstrap_ci(s, resamples=a.ci, seed=a.seed) for n, s in scores.items()}
        table = report.rows(scores, cis=cis)
        report.write_csv(os.path.join(a.out_dir, "scores.csv"), scores)
        md = report.markdown_table(table)
        with open(os.path.join(a.out_dir, "scores.md"), "w", encoding="utf-8") as fh:
            fh.write(md)
        for n, s in scores.items():
            s.to_json(os.path.join(a.out_dir, f"{n}.json"))
        print(md)
        return 0

    if a.cmd == "compare":
        from .stats import compare_systems
        comps = compare_systems(scores, a.measures, baseline=a.baseline, shuffles=a.shuffles,
                                resamples=a.resamples, seed=a.seed)
        md = report.comparisons_markdown(comps)
        with open(os.path.join(a.out_dir, "comparisons.md"), "w", encoding="utf-8") as fh:
            fh.write(md)
        with open(os.path.join(a.out_dir, "comparisons.json"), "w", encoding="utf-8") as fh:
            json.dump([c.as_dict() for c in comps], fh, indent=1)
        print(md)
        return 0

    if a.cmd == "profile":
        from .profile import profile_table, ranked_types
        types = ranked_types(a.ref, a.group, a.top)
        prof = profile_table(scores, group=a.group, types=types)
        prof = {t: prof[t] for t in types if t in prof}
        with open(os.path.join(a.out_dir, "profile.json"), "w", encoding="utf-8") as fh:
            json.dump(prof, fh, indent=1)
        report.heatmap(prof, os.path.join(a.out_dir, "profile.png"), systems=list(scores))
        print(f"profile written to {a.out_dir}/profile.png")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
