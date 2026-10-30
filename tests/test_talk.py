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
    assert talk.action({"guide": "bots"}, GAMES, {"section": "home"}) == {"web": "https://www.chess.com/play/computer"}  # in the app: the page itself
    assert talk.action({"guide": "the moon"}, GAMES, {"section": "home", "chesscom": "True"}) is None


def test_the_ai_s_order_in_any_shape_still_opens_the_game():
    """22 Oct hand test: "review my last game" -> the AI wrote {"do": "review 185351926500"} and nothing opened."""
    games = [{"n": 1, **GAMES[0]}, {"n": 2, **GAMES[1]}]
    for do in ("review 111", "review:111", {"review": 1}, {"review": "1"}, ["review", "111"], {"review": "anna"}):
        do = do if not isinstance(do, list) else " ".join(do)
        r = talk.reply("maya", "review my last game", home=HOME, games=games, ask_ai=ai_says({"say": "Here it is.", "do": do}))
        assert r["action"] == {"route": "games/111"}, do
    assert talk.action("open settings", games, None) == {"route": "settings"}
    assert talk.action("settings", games, None) == {"route": "settings"}


def test_my_second_last_game_is_number_two_and_a_made_up_game_is_refused():
    """"open the third last game review" -> the AI made up an id: now the games are numbered, and an id that
    isn't one of them is refused out loud, never "Sure, let's look at that game." with nothing opening."""
    games = [{"n": 1, **GAMES[0]}, {"n": 2, **GAMES[1]}]
    assert talk.action({"review": 2}, games, None) == {"route": "games/222"}
    r = talk.reply("maya", "open the third last game", home=HOME, games=games,
                   ask_ai=ai_says({"say": "Sure, let's look at that game.", "do": "review:145346368235"}))
    assert r["action"] is None and "can't find that game" in r["text"]


def test_an_order_without_words_says_what_it_did():
    """"open my game against hemmehra0416" -> {"do": "review …"} and no "say": a stock line about the habit came
    instead. Now the coach says what was opened."""
    r = talk.reply("maya", "open my game against anna", home=HOME, games=GAMES, ask_ai=ai_says({"do": "review 111"}))
    assert r["ai"] and r["action"] == {"route": "games/111"} and r["text"] == "Here's your game against anna, 13 Oct 2026."


def test_the_coach_is_told_the_games_by_number():
    import coach.talk as t
    rows = [{"id": str(i), "opponent": "x", "result": "win", "date": "d", "time_class": "rapid", "moments": 0, "checked": True}
            for i in range(30)]
    orig = t.insights.games_list
    t.insights.games_list = lambda: rows
    try:
        got = t.recent_games()
    finally:
        t.insights.games_list = orig
    assert [g["n"] for g in got] == list(range(1, talk.RECENT + 1)) and got[0]["id"] == "0"


def test_the_flat_answer_do_what_say():
    """The AI now answers {"do": "open", "what": "settings", "say": …}: it wrote {"do": "open"} with nothing to open
    when the order was nested (22 Oct)."""
    games = [{"n": 1, **GAMES[0]}, {"n": 2, **GAMES[1]}]
    cases = [({"do": "open", "what": "settings"}, {"route": "settings"}), ({"do": "review", "what": 2}, {"route": "games/222"}),
             ({"do": "review", "what": "anna"}, {"route": "games/111"}), ({"do": "rematch", "what": "1"}, None),
             ({"do": "none", "what": ""}, None), ({"do": "prep", "what": "Bob_99"}, {"route": "prep/bob_99"})]
    for order, want in cases:
        r = talk.reply("maya", "x", home=HOME, games=games, ask_ai=ai_says({**order, "say": "Okay."}))
        assert r["action"] == want or (want is None and order["do"] == "rematch"), order
    r = talk.reply("maya", "x", home=HOME, games=games, ask_ai=ai_says({"do": "open", "what": "", "say": "Opening it."}))
    assert r["action"] is None and "can't open that" in r["text"]


def test_an_unknown_word_opens_a_page_it_names_and_is_otherwise_just_talk():
    assert talk.action({"do": "show", "what": "level"}, GAMES, None) == {"route": "level"}
    r = talk.reply("maya", "how do I get better", home=HOME, games=GAMES,
                   ask_ai=ai_says({"do": "advice", "what": "habits", "say": "Keep every piece safe, one move at a time."}))
    assert r["action"] is None and r["text"].startswith("Keep every piece safe")


def test_a_wrong_order_is_tried_once_more_told_why():
    """"open my second last game" -> {"do": "review", "what": "second last"}: asked again, it answers 2."""
    answers = iter([{"do": "review", "what": "second last", "say": "Here it is."}, {"do": "review", "what": 2, "say": "Here it is."}])
    seen = []

    def ai(system, prompt, n):
        seen.append(prompt)
        return json.dumps(next(answers)), "groq"
    games = [{"n": 1, **GAMES[0]}, {"n": 2, **GAMES[1]}]
    r = talk.reply("maya", "open my second last game", home=HOME, games=games, ask_ai=ai)
    assert r["action"] == {"route": "games/222"} and len(seen) == 2 and "could not be done" in seen[1]


def test_busy_keys_are_said_plainly():
    """22 Oct: with both free keys at their limit she answered every question with the habit line."""
    def busy(*a):
        raise RuntimeError("groq: HTTP 429; gemini: HTTP 429")
    r = talk.reply("maya", "tell me a joke", home=HOME, games=GAMES, ask_ai=busy)
    assert r["text"] == talk.BUSY and r["action"] is None and not r["ai"]


def test_next_and_back_whatever_follows_the_word():
    for do in ({"do": "next", "what": "step"}, {"do": "next", "what": "move"}, {"next": 1}, "next"):
        assert talk.action(do, [], {"section": "review"}) == {"next": True}
    assert talk.action({"do": "back", "what": "previous move"}, [], {"section": "review"}) == {"back": True}


def test_a_word_that_is_not_an_action_keeps_the_real_answer_and_prep_says_what_it_needs():
    # cloud review 26 Oct: "do": "talk" used to replace the answer with "I can't open that from here"
    for do in ("talk", "answer", "no action"):
        r = talk.reply("maya", "how do I stop hanging pieces?", home=HOME, games=GAMES,
                       ask_ai=ai_says({"say": "Keep every piece safe: check what they can take.", "do": do}))
        assert r["text"].startswith("Keep every piece safe") and r["action"] is None
    r = talk.reply("maya", "prep against Magnus Carlsen", home=HOME, games=GAMES,
                   ask_ai=ai_says({"say": "Let's prep.", "do": "prep", "what": "Magnus Carlsen"}))
    assert r["text"] == talk.REFUSED["prep"]


def test_a_refused_key_and_no_internet_are_said_as_such():
    def refused(*a):
        raise RuntimeError("groq: HTTP 401")
    assert talk.reply("maya", "hi", home=HOME, games=GAMES, ask_ai=refused)["text"] == talk.KEY_REFUSED


def test_the_coach_knows_how_the_last_game_ended(monkeypatch):
    """30 Oct test: "why did my opponent resign the last game" got "I don't have the engine details for that game".
    The coach is now told how each game ended and, for the last one, the material at the end."""
    url = "https://www.chess.com/game/live/9"
    pgn = '[Event "x"]\n\n1. e4 e5 2. Qh5 Nc6 3. Qxf7+ Kxf7 4. Nf3 d6 1-0'  # white gave up the queen, then they resigned
    row = {"id": "9", "url": url, "opponent": "x", "opponent_rating": 400, "result": "win", "date": "d",
           "time_class": "rapid", "opening": None, "moves": 4, "pieces_lost": 1, "moments": 0, "checked": True,
           "color": "black", "how": "resigned"}
    monkeypatch.setattr(talk.insights, "games_list", lambda: [row, {**row, "id": "8", "result": "loss", "how": "timeout"}])
    monkeypatch.setattr(talk.insights, "_games", lambda: [{"url": url, "pgn": pgn}])
    monkeypatch.setattr(talk.insights, "_moves", lambda: {})
    last, before = talk.recent_games()[:2]
    assert last["ended"] == "they resigned" and before["ended"] == "you ran out of time"
    assert last["material_at_the_end"].startswith("you were 8 points ahead")  # a queen for a pawn
    assert talk.ended({"how": "repetition", "result": "draw"}) == "draw by repetition"
