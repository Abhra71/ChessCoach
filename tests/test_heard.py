"""What the coach heard, kept as text (flagship 6): kept, capped, deleted, and the names it learns."""
from coach import heard, talk
from tests.test_talk import GAMES, HOME, ai_says


def test_lines_are_kept_newest_first_and_deleted():
    heard.note("Review my game against El Moungabs.", "groq")
    heard.note("  Next.  ", "groq")
    assert heard.count() == 2 and heard.recent()[0]["text"] == "Next."
    heard.forget()
    assert heard.count() == 0 and heard.words() == []


def test_the_name_talk_worked_out_is_learned_for_the_hearing():
    """'El Moungabs' was heard, the review of lmaongabs opened: next time the hearing expects lmaongabs."""
    g = GAMES[0]
    talk.reply("maya", "review my game against el moungabs", home=HOME, games=GAMES,
               ask_ai=ai_says({"say": "Here it is.", "do": {"review": g["id"]}}))
    talk.reply("maya", "prepare me against hem mehra", home=HOME, games=GAMES,
               ask_ai=ai_says({"say": "Let's prepare.", "do": {"prep": "hemmehra0416"}}))
    assert set(heard.words()) == {g["opponent"], "hemmehra0416"}
