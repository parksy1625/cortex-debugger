import json

from cortex_engine.cli import main


def test_info(capsys):
    assert main(["info"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["stage"] == "M7"


def test_score(capsys):
    assert main(["score", "--clean", "2", "--corrupted", "0", "--patched", "1"]) == 0
    assert json.loads(capsys.readouterr().out)["recovery"] == 0.5


def test_nonfinite_error(capsys):
    assert main(["score", "--clean", "nan", "--corrupted", "0", "--patched", "1"]) == 2
    assert '"status": "error"' in capsys.readouterr().err


def test_pair_rejects_bad_revision(capsys):
    assert main([
        "pair", "--clean", "ab", "--corrupted", "cd",
        "--correct-token", " yes", "--incorrect-token", " no",
        "--layer", "0", "--token-index", "0", "--revision", "main",
    ]) == 2
    assert "revision" in capsys.readouterr().err
