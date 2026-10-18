import json
import os

from geclens.cli import main


def test_cli_subset_and_score(data, tmp_path):
    out = tmp_path / "s.json"
    assert main(["subset", "--ref", os.path.join(data, "ref.m2"), "--type", "PREP", "--out", str(out)]) == 0
    assert json.load(open(out, encoding="utf-8"))["selector"] == "PREP"
    od = tmp_path / "res"
    assert main(["score", "--src", os.path.join(data, "src.txt"), "--ref", os.path.join(data, "ref.m2"),
                 "--hyp", f"careful={os.path.join(data, 'careful.txt')}", "--out-dir", str(od)]) == 0
    assert (od / "scores.csv").exists() and (od / "careful.json").exists()


def test_cli_profile(data, tmp_path):
    od = tmp_path / "prof"
    assert main(["profile", "--src", os.path.join(data, "src.txt"), "--ref", os.path.join(data, "ref.m2"),
                 "--hyp", os.path.join(data, "careful.txt"), os.path.join(data, "eager.txt"),
                 "--out-dir", str(od), "--top", "5"]) == 0
    assert (od / "profile.png").exists()
