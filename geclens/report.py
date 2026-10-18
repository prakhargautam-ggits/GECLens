"""Tables (CSV, Markdown, LaTeX) and figures for GECLens results.

Figures follow a restrained style: one hue for magnitude (light to dark blue), thin marks, direct labels, recessive grid,
no dual axes. Matplotlib is imported lazily so the scoring API does not depend on a display.
"""
from __future__ import annotations

import csv
import math
from typing import Dict, List, Optional, Sequence

from .score import SystemScore

SEQ_BLUE = ["#f4f8fd", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#2a78d6", "#1c5cab", "#104281", "#0d366b"]
SERIES_1 = "#2a78d6"
INK, INK_2, GRID = "#1f1f1e", "#5c5b55", "#e4e3de"

DEFAULT_COLUMNS = [
    ("overall", "F0.5", "Overall F0.5"),
    ("type", "F0.5", "Type F0.5"),
    ("type_only", "F0.5", "Type-only F0.5"),
    ("detection", "F1", "Detection F1"),
    ("success", "rate", "Success"),
    ("overcorrection", "rate", "Over-corr."),
]


def _fmt(v, pct: bool = False) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "n/a"
    return f"{100 * v:.1f}%" if pct else f"{v:.3f}"


def rows(scores: Dict[str, SystemScore], columns=DEFAULT_COLUMNS, cis: Optional[Dict[str, dict]] = None) -> List[dict]:
    out = []
    for name, sc in scores.items():
        r = {"System": name}
        for measure, key, label in columns:
            v = sc.metrics[measure][key]
            pct = key == "rate"
            cell = _fmt(v, pct)
            if cis and name in cis and measure in cis[name]:
                lo, hi = cis[name][measure]
                cell += f" [{_fmt(lo, pct)}, {_fmt(hi, pct)}]"
            r[label] = cell
        out.append(r)
    return out


def write_csv(path: str, scores: Dict[str, SystemScore], columns=DEFAULT_COLUMNS) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["system", "selector"] + [f"{m}_{k}" for m, k, _ in columns])
        for name, sc in scores.items():
            w.writerow([name, sc.selector] + [sc.metrics[m][k] for m, k, _ in columns])


def markdown_table(table_rows: List[dict]) -> str:
    if not table_rows:
        return ""
    head = list(table_rows[0])
    lines = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    lines += ["| " + " | ".join(str(r[h]) for h in head) + " |" for r in table_rows]
    return "\n".join(lines) + "\n"


def latex_table(table_rows: List[dict], caption: str = "", label: str = "tab:geclens") -> str:
    if not table_rows:
        return ""
    head = list(table_rows[0])
    esc = lambda s: str(s).replace("%", r"\%").replace("_", r"\_").replace("&", r"\&")
    out = [r"\begin{table}[t]", r"\centering", r"\begin{tabular}{l" + "r" * (len(head) - 1) + "}", r"\hline",
           " & ".join(esc(h) for h in head) + r" \\", r"\hline"]
    out += [" & ".join(esc(r[h]) for h in head) + r" \\" for r in table_rows]
    out += [r"\hline", r"\end{tabular}"]
    if caption:
        out.append(r"\caption{" + esc(caption) + "}")
    out += [r"\label{" + label + "}", r"\end{table}"]
    return "\n".join(out) + "\n"


def comparisons_markdown(comps) -> str:
    rows_ = [{"A": c.a, "B": c.b, "Measure": c.measure, "Diff (A-B)": f"{c.diff:+.3f}",
              "95% CI": "n/a" if c.ci is None else f"[{c.ci[0]:+.3f}, {c.ci[1]:+.3f}]",
              "p": f"{c.p:.4f}", "p (Holm)": f"{c.p_holm:.4f}"} for c in comps]
    return markdown_table(rows_)


def _style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK_2)
        ax.spines[s].set_linewidth(0.8)
    ax.tick_params(colors=INK_2, labelsize=8)
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def scatter_plot(scores: Dict[str, SystemScore], path: str, y_measure: str = "type_only",
                 x_measure: str = "overcorrection", title: Optional[str] = None) -> None:
    """Type-level F0.5 (y) against over-correction on unedited sentences (x); one labelled dot per system."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5.2, 3.6), dpi=200)
    xs, ys, names = [], [], []
    for name, sc in scores.items():
        x = sc.metrics[x_measure]["rate"] * 100
        y = sc.metrics[y_measure]["F0.5"] if "F0.5" in sc.metrics[y_measure] else sc.metrics[y_measure]["rate"]
        xs.append(x); ys.append(y); names.append(name)
    ax.scatter(xs, ys, s=36, color=SERIES_1, edgecolor="white", linewidth=1.2, zorder=3)
    for x, y, n in zip(xs, ys, names):
        ax.annotate(n, (x, y), xytext=(5, 3), textcoords="offset points", fontsize=7, color=INK)
    _style(ax)
    ax.set_xlabel("Over-correction on unedited sentences (%)", fontsize=8, color=INK)
    ax.set_ylabel(f"{y_measure.replace('_', '-')} F0.5", fontsize=8, color=INK)
    ax.set_xlim(left=0)
    if title:
        ax.set_title(title, fontsize=9, color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def heatmap(profile: Dict[str, Dict[str, dict]], path: str, value: str = "F", systems: Optional[Sequence[str]] = None,
            title: Optional[str] = None, annotate: bool = True) -> None:
    """System x error-type heatmap of ERRANT F0.5 (one hue, light = low, dark = high)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    import numpy as np

    types = list(profile)
    systems = list(systems or next(iter(profile.values())).keys())
    M = np.array([[profile[t][s][value] for t in types] for s in systems], dtype=float)
    cmap = LinearSegmentedColormap.from_list("geclens_blue", SEQ_BLUE)
    w = max(4.5, 0.42 * len(types) + 2.2)
    h = max(2.0, 0.34 * len(systems) + 1.2)
    fig, ax = plt.subplots(figsize=(w, h), dpi=200)
    im = ax.imshow(M, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(types)))
    ax.set_xticklabels(types, rotation=55, ha="right", fontsize=7, color=INK)
    ax.set_yticks(range(len(systems)))
    ax.set_yticklabels(systems, fontsize=7, color=INK)
    ax.set_xticks(np.arange(-.5, len(types), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(systems), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.5)
    ax.tick_params(which="both", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    if annotate:
        for i in range(len(systems)):
            for j in range(len(types)):
                v = M[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=5.5,
                        color="white" if v >= 0.55 else INK)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.ax.tick_params(labelsize=6, colors=INK_2)
    cb.outline.set_visible(False)
    cb.set_label(f"{value}0.5" if value == "F" else value, fontsize=7, color=INK)
    if title:
        ax.set_title(title, fontsize=9, color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
