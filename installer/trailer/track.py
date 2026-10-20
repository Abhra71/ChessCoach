"""Beat tracking (Ellis 2007, dynamic programming) on the onset curves from beats.mjs; then which beat starts a bar."""
import json
import math
import sys

import numpy as np


def track(O, bpm, a, b, tight=100.0):
    O = np.asarray(O[a:b], float)
    O = O / (O.std() + 1e-9)
    p = 6000.0 / bpm  # frames (10 ms) per beat
    n = len(O)
    score = O.copy()
    back = -np.ones(n, int)
    lo, hi = int(round(p / 2)), int(round(2 * p))
    for i in range(hi, n):
        js = np.arange(i - hi, i - lo + 1)
        pen = -tight * np.log((i - js) / p) ** 2
        k = np.argmax(score[js] + pen)
        score[i] = O[i] + score[js[k]] + pen[k]
        back[i] = js[k]
    i = int(np.argmax(score[n - hi:]) + n - hi)
    beats = []
    while i >= 0:
        beats.append(i)
        i = back[i]
    return [(x + a) / 100 for x in reversed(beats)], O


def bars(beats, O, a, per=4):
    """Which of the 4 beat positions is the first of a bar: the one with the strongest hits."""
    s = [0.0] * per
    for k, t in enumerate(beats):
        i = int(round(t * 100)) - a
        s[k % per] += max(O[max(0, i - 2):i + 3]) if 0 <= i < len(O) else 0
    return int(np.argmax(s)), [round(v, 1) for v in s]


song, bpm, a, b = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
d = json.load(open(f"beats-{song}.json"))
A, B = int(a * 100), int(b * 100)
beats, O = track(d["onset"], bpm, A, B)
first, s = bars(beats, O, A)
iv = np.diff(beats)
print(song, "beats", len(beats), "mean interval", round(float(iv.mean()), 4), "=", round(60 / float(iv.mean()), 2), "bpm; spread", round(float(iv.std()), 4))
print("bar strength by position", s, "-> bars start at beat", first)
print("downbeats", [beats[k] for k in range(first, len(beats), 4)])
json.dump({"beats": beats, "first": first}, open(f"grid-{song}.json", "w"))
