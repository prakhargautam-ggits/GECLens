"""GECLens: error-type-targeted evaluation of grammatical error correction systems."""

__version__ = "1.0.1"

from .types import TypeSelector  # noqa: E402,F401
from .data import Subsets, build_subsets, reference_stats  # noqa: E402,F401
from .score import SystemScore, score_system  # noqa: E402,F401
from .stats import approx_randomisation, bootstrap_ci, compare_systems, holm, paired_bootstrap_ci  # noqa: E402,F401
from .profile import profile_table  # noqa: E402,F401
from .pipeline import evaluate, score_many  # noqa: E402,F401

__all__ = ["TypeSelector", "Subsets", "build_subsets", "reference_stats", "SystemScore", "score_system",
           "approx_randomisation", "bootstrap_ci", "compare_systems", "holm", "paired_bootstrap_ci", "profile_table",
           "evaluate", "score_many", "__version__"]
