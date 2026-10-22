"""Near silence is never sent to be heard, and Whisper's no-speech parts are dropped (22 Oct test)."""
from array import array

from coach import ai


def test_silence_is_not_heard():
    quiet = array("h", [0, 12, -30, 40] * 4000).tobytes()
    assert not ai.loud_enough(quiet)
    assert ai.hear(quiet, hearers={"groq": lambda k, a: "Subtitles by the Amara.org community"}) == ("", None)


def test_speech_is_loud_enough():
    assert ai.loud_enough(array("h", [0, 8000, -9000, 100] * 4000).tobytes())
