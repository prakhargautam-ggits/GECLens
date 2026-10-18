import json
import os

import yaml

from geclens.config import run_config
from geclens.report import latex_table, markdown_table, rows


def test_yaml_runner_end_to_end(data, tmp_path):
    cfg = {"source": os.path.join(data, "src.txt"), "reference": os.path.join(data, "ref.m2"),
           "out_dir": str(tmp_path / "out"), "selectors": ["R:VERB:SVA", "PREP"],
           "systems": {n: os.path.join(data, f"{n}.txt") for n in ("careful", "eager", "cautious")},
           "statistics": {"bootstrap_resamples": 200, "shuffles": 500, "baseline": "cautious"},
           "profile": {"group": "category", "top": 5}}
    p = tmp_path / "c.yaml"
    p.write_text(yaml.safe_dump(cfg))
    res = run_config(str(p))
    assert set(res) == {"R:VERB:SVA", "PREP"}
    d = tmp_path / "out" / "R_VERB_SVA"
    for f in ("scores.csv", "scores.md", "scores.tex", "comparisons.md", "confidence_intervals.json",
              "scatter.png", "profile.png", "subsets.json"):
        assert (d / f).exists(), f
    comps = json.load(open(d / "comparisons.json", encoding="utf-8"))
    assert len(comps) == 4 and all(c["b"] == "cautious" for c in comps)


def test_tables(toy_scores):
    r = rows(toy_scores)
    md, tex = markdown_table(r), latex_table(r, caption="x")
    assert md.count("\n") == len(r) + 2
    assert "\\begin{tabular}" in tex and "careful" in tex
