import os
import pytest

DATA = os.path.join(os.path.dirname(__file__), "data")


@pytest.fixture(scope="session")
def data():
    return DATA


@pytest.fixture(scope="session")
def toy_scores(tmp_path_factory):
    from geclens.pipeline import score_many
    cache = str(tmp_path_factory.mktemp("cache"))
    systems = {n: os.path.join(DATA, f"{n}.txt") for n in ("careful", "eager", "cautious")}
    return score_many(os.path.join(DATA, "src.txt"), os.path.join(DATA, "ref.m2"), systems, "R:VERB:SVA",
                      cache_dir=cache, verbose=False)
