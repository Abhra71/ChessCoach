"""Opponents' names never go to the AI company, yet the player still reads them and can ask by name, even misspelled
(owner, 28 Nov 2026: "would it stop the AI from mentioning real names? if yes, don't do it")."""
import json

import pytest

from coach import coaches, plan, privacy, talk

GAMES = [{"n": 1, "id": "111", "opponent": "SreejitDebnath", "result": "loss", "date": "27 Nov 2026", "moments": 2},
         {"n": 2, "id": "222", "opponent": "salmonetetete", "result": "loss", "date": "26 Nov 2026", "moments": 1},
         {"n": 3, "id": "333", "opponent": "king", "result": "win", "date": "25 Nov 2026", "moments": 0}]
HOME = {"player": "me", "rating": 400, "last_game": {"opponent": "SreejitDebnath", "result": "loss"},
        "focus": {"pattern": "left a piece hanging", "habit": "Check every piece."}}
REAL = ("sreejit", "sreejt", "salmonetetete")  # "sreejt": the player's own typo must not reach the AI either


@pytest.fixture(autouse=True)
def _quiet(monkeypatch):
    monkeypatch.setattr(talk, "_LAST", {})
    monkeypatch.setattr(talk.insights, "games_list", lambda: [])
    monkeypatch.setattr(talk.insights, "extras_for", lambda gid: {"rematch": {"ply": 17}})


def spy(answer):
    """A pretend AI that keeps everything it was sent."""
    sent = []

    def ask(system, prompt, n):
        sent.append(system + "\n" + prompt)
        return (json.dumps(answer) if not isinstance(answer, str) else answer), "groq"
    return ask, sent


def test_swap_and_swap_back():
    a = privacy.Aliases(["SreejitDebnath", "salmonetetete"])
    assert a.hide("lost to sreejitdebnath and SALMONETETETE") == "lost to Opponent A and Opponent B"
    assert a.show("Opponent A's queen; opponent b too") == "SreejitDebnath's queen; salmonetetete too"
    assert a.show({"do": {"rematch": "Opponent B"}}) == {"do": {"rematch": "salmonetetete"}}


def test_a_typed_name_close_or_split_is_swapped_but_everyday_words_never():
    a = privacy.Aliases(["SreejitDebnath", "salmonetetete", "gamer123"])
    assert a.hide_said("rematch sreejt") == "rematch Opponent A"  # a typo (19 Nov: "just close")
    assert a.hide_said("my game vs sreejit debnath") == "my game vs Opponent A"  # two words for one name
    assert a.hide_said("why did salmon win") == "why did Opponent B win"  # the start of a name
    assert a.hide_said("open my last games please") == "open my last games please"  # "games" is not gamer123
    assert a.hide_said("Opponent B again") == "Opponent B again"


def test_the_ask_box_sends_no_names_but_the_player_reads_them_and_the_rematch_opens():
    ask, sent = spy({"say": "Against Opponent A it went wrong at move 9. Let's play it again.",
                     "do": {"rematch": "Opponent A"}})
    r = talk.reply("maya", "rematch my game against sreejt", home=HOME, games=GAMES, ask_ai=ask)
    assert not any(n in sent[0].lower() for n in REAL), "a real name went to the AI"
    assert "Opponent A" in sent[0] and "Opponent B" in sent[0]
    assert r["text"] == "Against SreejitDebnath it went wrong at move 9. Let's play it again."
    assert r["action"] == {"route": "rematch/111/17"}


def test_a_name_that_is_an_everyday_word_still_hides_its_opponent_field():
    ask, sent = spy({"say": "Fine.", "do": None})
    talk.reply("maya", "how is my king safety", home=HOME, games=GAMES, ask_ai=ask)
    facts = json.loads(sent[0].split("Facts:\n", 1)[1].split("\n\n", 1)[0])
    assert [g["opponent"] for g in facts["recent_games"]] == ["Opponent A", "Opponent B", "Opponent C"]
    assert "king safety" in sent[0]  # the word itself is left alone


def test_the_chesscom_chat_and_the_weekly_idea_send_no_names(monkeypatch):
    ask, sent = spy("Against Opponent A you rushed. Slow down.")
    r = coaches.chat("maya", "why did I lose to sreejit", home=HOME, ask_ai=ask)
    assert not any(n in sent[0].lower() for n in REAL) and r["text"] == "Against SreejitDebnath you rushed. Slow down."
    ask2, sent2 = spy({"title": "Breathe before you move", "text": "Take one breath. Then check every piece."})
    monkeypatch.setattr(plan, "_memory", lambda: {})
    monkeypatch.setattr(plan, "_update", lambda f: None)
    monkeypatch.setattr(plan, "_practised", lambda idea, rating, rng: idea)
    plan.ai_idea(HOME, ask_ai=ask2)
    assert sent2 and not any(n in sent2[0].lower() for n in REAL)
