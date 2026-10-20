import json

from coach import talk

GAMES = [{"id": "111", "opponent": "anna", "result": "loss", "date": "13 Oct 2026", "time_class": "rapid", "moments": 2},
         {"id": "222", "opponent": "bob", "result": "win", "date": "12 Oct 2026", "time_class": "rapid", "moments": 0}]
HOME = {"player": "me", "rating": 254, "focus": {"pattern": "left a piece hanging", "habit": "Check every piece."}}


def ai_says(obj):
    return lambda system, prompt, n: (json.dumps(obj) if not isinstance(obj, str) else obj, "groq")


def test_the_coach_opens_the_game_it_was_asked_for():
    r = talk.reply("maya", "review my game against anna", home=HOME, games=GAMES,
                   ask_ai=ai_says({"say": "Let's look at it together.", "do": {"review": "111"}}))
    assert r["ai"] and r["action"] == {"route": "games/111"} and r["text"] == "Let's look at it together."


def test_a_game_or_page_it_was_not_told_about_is_refused():
    assert talk.reply("maya", "x", home=HOME, games=GAMES, ask_ai=ai_says({"say": "Okay.", "do": {"review": "999"}}))["action"] is None
    assert talk.reply("maya", "x", home=HOME, games=GAMES, ask_ai=ai_says({"say": "Okay.", "do": {"open": "secret"}}))["action"] is None
    assert talk.action({"open": "plan"}, GAMES, None) == {"route": "plan"}


def test_next_step_only_on_a_review():
    assert talk.action({"next": True}, GAMES, {"section": "review"}) == {"next": True}
    assert talk.action({"next": True}, GAMES, {"section": "home"}) is None


def test_no_rematch_of_a_won_game():
    assert talk.action({"rematch": "222"}, GAMES, None) is None


def test_a_refused_action_is_never_promised():
    """19 Oct: "Rematch it" on Home said "Let's replay that game." and nothing happened."""
    r = talk.reply("maya", "rematch it", home=HOME, games=GAMES,
                   ask_ai=ai_says({"say": "Let's replay that game.", "do": {"rematch": "222"}}))
    assert r["action"] is None and "can't start a rematch from here" in r["text"]


def test_prep_against_any_player_but_only_a_real_username():
    assert talk.action({"prep": "Hemmehra0416"}, GAMES, None) == {"route": "prep/hemmehra0416"}
    assert talk.action({"prep": "../settings"}, GAMES, None) is None


def test_json_wrapped_in_words_is_still_read_and_nonsense_falls_back():
    assert talk.parse('Sure! ```json\n{"say": "Hi.", "do": null}\n```')["say"] == "Hi."
    r = talk.reply("viktor", "hello", home=HOME, games=GAMES, ask_ai=ai_says("not json at all"))
    assert not r["ai"] and r["action"] is None and r["text"]


def test_without_a_key_the_conversation_goes_on():
    def no_key(*a):
        raise RuntimeError("no key")
    r = talk.reply("maya", "hello", home=HOME, games=GAMES, ask_ai=no_key)
    assert not r["ai"] and r["text"] and r["action"] is None


def test_a_square_the_facts_dont_have_is_not_said():
    r = talk.reply("maya", "what now", home=HOME, games=GAMES, ask_ai=ai_says({"say": "Move your knight to f5.", "do": None}))
    assert not r["ai"]


def test_the_red_ring_only_on_chess_com_and_only_to_known_places():
    """"Take me to the bots": the ring on chess.com; in the app it says where to ask; an unknown place does nothing."""
    g = talk.action({"guide": "bots"}, GAMES, {"section": "home", "chesscom": "True"})
    assert g["guide"]["to"] == "/play/computer" and g["guide"]["steps"][0]["path"] == "/play"
    assert talk.action({"guide": "bots"}, GAMES, {"section": "home"}) is None
    assert talk.action({"guide": "the moon"}, GAMES, {"section": "home", "chesscom": "True"}) is None
