from geclens.m2 import apply_edits, parse_block

BLOCK = "S She go to school .\nA 1 2|||R:VERB:SVA|||goes|||REQUIRED|||-NONE-|||0\nA -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||1"


def test_parse_keeps_noop_annotator():
    s = parse_block(BLOCK)
    assert s.source == ["She", "go", "to", "school", "."]
    assert s.edits == {0: [(1, 2, "R:VERB:SVA", "goes")], 1: []}
    assert not s.is_unedited()


def test_apply_edits():
    s = parse_block(BLOCK)
    assert apply_edits(s.source, s.edits[0]) == ["She", "goes", "to", "school", "."]
    assert apply_edits(["a", "b", "c"], [(1, 2, "U:X", "-NONE-"), (3, 3, "M:X", "d")]) == ["a", "c", "d"]
