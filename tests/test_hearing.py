import numpy as np

from coach import hearing


def test_resample_to_16k_keeps_length_in_time():
    one_second_24k = np.zeros(24000, dtype=np.float32)
    assert len(hearing.resample(one_second_24k, 24000)) == 16000
    assert len(hearing.resample(np.zeros(16000), 16000)) == 16000


def test_silence_too_short_is_nothing():
    assert hearing.transcribe(np.zeros(1000, dtype=np.float32)) == ""
