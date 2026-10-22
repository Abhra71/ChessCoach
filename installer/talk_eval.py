"""How reliable is talking to the coach? Real phrasings, each with what must happen, run through the real AI with the
test copy's keys (try test). python installer/talk_eval.py [rounds]   -> a score per phrasing, and every reply for off-topic ones."""
import json
import os
import sys
import time

os.environ["KNIGHTWISE_HOME"] = os.path.join(os.environ["TEMP"], "knightwise-test")
os.environ["KNIGHTWISE_VAULT"] = "Knightwise-test"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from coach import ai, talk  # noqa: E402

G = {g["n"]: g["id"] for g in talk.recent_games()}
LOST = next(g for g in talk.recent_games() if g["result"] == "loss")
# (what the player says, the route that must open, or None for "nothing opens")
DO = [
    ("review my last game", f"games/{G[1]}"),
    ("open the last game review. actually open the third last game review.", f"games/{G[3]}"),
    ("open my game against hemmehra0416", "games/185261729330"),
    ("show me the game I lost against hemmehra", "games/185261729330"),
    ("can you open my second last game", f"games/{G[2]}"),
    ("Can you change your settings for me?", "settings"),
    ("open settings", "settings"),
    ("take me to my plan", "plan"),
    ("show me my level", "level"),
    ("open my course", "course"),
    ("i want to practise", "practice"),
    ("let's do today's five minutes", "daily"),
    ("how am I doing lately, show me my progress", "progress"),
    ("go home", "home"),
    ("rematch my game against hemmehra0416", "rematch/185261729330"),
    ("prep against hemmehra0416", "prep/hemmehra0416"),
    ("I'm playing magnuscarlsen next, help me prepare", "prep/magnuscarlsen"),
    ("open the endgame trainer", "endgames"),
]
TALK = [  # nothing should open; the reply must be kind, short, and about chess or say what it can't do
    "what can I do with my voice in this app?",
    "how do I get better like a strong player?",
    "what's the weather today?",
    "tell me a joke",
    "can you do my maths homework?",
    "who is the best chess player ever?",
    "you're useless",
    "I feel sad, I keep losing",
    "what's your name?",
    "write me a poem about pizza",
    "what's my rating?",
    "delete all my games",
]


def run(rounds):
    score, out = {}, []
    for k in range(rounds):
        for said, want in DO + [(t, None) for t in TALK]:
            r = talk.reply("maya", said, [], {"section": "home"})
            got = (r.get("action") or {}).get("route")
            ok = (got or "").startswith(want) if want else got is None
            score.setdefault(said, []).append(ok)
            out.append({"said": said, "want": want, "got": got, "ai": r["ai"], "text": r["text"], "model": dict(ai._MODELS)})
            time.sleep(6)
    return score, out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    score, out = run(rounds)
    json.dump(out, open("talkeval-out.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    actions = [s for s, _ in DO]
    a_ok = sum(sum(score[s]) for s in actions); a_n = sum(len(score[s]) for s in actions)
    t_ok = sum(sum(score[s]) for s in TALK); t_n = sum(len(score[s]) for s in TALK)
    print(f"ACTIONS right: {a_ok}/{a_n}   TALK (nothing opened): {t_ok}/{t_n}   models: {out[-1]['model']}")
    for s, oks in score.items():
        if not all(oks):
            bad = [o for o in out if o["said"] == s and not ((o["got"] or "").startswith(o["want"]) if o["want"] else o["got"] is None)]
            print(f"  FAIL {sum(oks)}/{len(oks)}  {s!r}: got {bad[0]['got']} ai={bad[0]['ai']} -> {bad[0]['text'][:110]!r}")
    print("\nOFF-TOPIC replies:")
    for o in out:
        if o["said"] in TALK:
            print(f"  {o['said']!r}: {o['text'][:170]!r} (ai={o['ai']})")
