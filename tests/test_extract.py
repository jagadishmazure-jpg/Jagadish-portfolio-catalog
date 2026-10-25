from catalog import extract as X

MD = "# T\n\n[![b](x)](y)\n\nThis paragraph explains the whole project in enough words to count.\n\n## Architecture\n\nboxes\n\n```\n# not a heading\n```\n\n## Results\n\n- recall@5 0.633 to 0.933 on 30 questions\n- nothing numeric here at all, just words\n"


def test_sections_ignore_fenced_headings():
    heads = [h for h, _, _ in X.sections(MD)]
    assert "not a heading" not in heads and "Architecture" in heads


def test_pick_and_intro():
    assert X.pick(MD, "architecture").startswith("boxes")
    assert X.intro(MD).startswith("This paragraph")
    assert X.pick(MD, "limitations") == ""


def test_results_need_number_and_metric():
    res = X.results(MD)
    assert res == ["recall@5 0.633 to 0.933 on 30 questions"]


def test_evidence_board_prefers_evidence():
    assert X.evidence_board(["a/board.png", "docs/evidence_board.png", "x.py"]) == "docs/evidence_board.png"
    assert X.evidence_board(["x.py"]) is None
