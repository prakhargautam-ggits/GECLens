from geclens.types import TypeSelector


def test_exact():
    s = TypeSelector("R:VERB:SVA")
    assert s("R:VERB:SVA") and not s("M:VERB:SVA") and not s("noop")


def test_category_expands_to_operations():
    s = TypeSelector("DET")
    assert s("M:DET") and s("R:DET") and s("U:DET") and not s("R:PREP")


def test_pattern_and_list():
    s = TypeSelector("R:VERB*,PREP")
    assert s("R:VERB:SVA") and s("R:VERB:TENSE") and s("U:PREP") and not s("M:VERB:FORM")
