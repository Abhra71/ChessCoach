from coach.voice import sentences, speakable, tidy_leftovers


def test_moves_are_read_as_words():
    assert speakable("Better: Nf3. You played Qxd4+.") == "Better: knight f3. You played queen takes d4, check."
    assert speakable("O-O-O then O-O") == "castles long then castles"
    assert speakable("exd8=Q#") == "e takes d8 promotes to queen, checkmate"


def test_plain_words_untouched():
    assert speakable("After c3, their queen on d5 can take your bishop on d3.") == \
        "After c3, their queen on d5 can take your bishop on d3."


def test_sentences():
    assert sentences("Move 4. After c3, their queen can take it! Better: Nf3.") == \
        ["Move 4.", "After c3, their queen can take it!", "Better: Nf3."]


def test_tidy_leftovers_only_removes_the_speech_library_copies(tmp_path):
    for name, files in [("tmpa", ["espeak-ng.dll"]), ("tmpb", ["espeak-ng.dll", "other.txt"]), ("keep", ["espeak-ng.dll"])]:
        (tmp_path / name).mkdir()
        for f in files:
            (tmp_path / name / f).write_text("x")
    assert tidy_leftovers(tmp_path) == 1
    assert sorted(p.name for p in tmp_path.iterdir()) == ["keep", "tmpb"]
