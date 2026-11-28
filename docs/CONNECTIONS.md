# The connection system: every feature reaches the player at the right time (design, 28 Nov 2026)

Owner's rule: players come to *view*; the coaches make them want to use the app. Every feature must be brought to
the player at the right time, not all at once, and nothing we build may sit unused. This is the system that
makes sure, and keeps track. Status: **design for the owner; not built yet.**

## What exists today (coach/nudge.py)
- **The tour:** 22 features, each introduced once, up to 3 a day, 20 minutes apart.
- **Data-driven suggestions:** 14 kinds come from the player's games: today's 5 minutes, a new game, rematch, the
  clock drill, the next lesson, endgames (stalemates, conversion), the worst opening, In your head (deep tricks),
  repertoire, prep, badges, the week, bots, chess.com.
- **Limits:** at most 3 a day per place, 10 minutes apart, never during a live game, never in a review.

## What's missing
1. **Once opened, never again.** Most data-driven suggestions stop for good once the player has opened the page
   ("not opened" in 9 places). If the clock problem comes back in March, Maya stays silent.
2. **No feature list in one place.** Each suggestion is code in nudge.py; nothing says "this feature exists, these
   are its moments, this is its story, this data feeds it", so a new feature can be forgotten.
3. **No record of use.** The app knows a page was *opened*, not how often a feature is *used*, when last, or whether
   it *helped* (did the habit number improve?).
4. **No coverage view.** Nobody can see which features this player has never used, or which ones every player
   ignores.
5. **Some features have no moment at all:** Blindfold, Guess the move, Game of the month, Wrapped.

## The system: five parts

### 1. The feature map (one file, coach/features.py)
Every feature listed once: its page, its coach, its reason in the story (docs/STORYLINE.md), the data it uses, and
its **moments**: small functions that read the player's data and answer "how much does this player need this now?"
(0 = not at all, 1 = urgently) with the line the coach says.

### 2. The use record (data/features.json)
For each feature, for this player: first brought up, last brought up, times opened, times used to the end, last
used, and the habit number it targets before and after (so we know whether it helped).

### 3. The picker (the coaches' brain, replacing "once opened, never again")
Each day it scores every feature:
**need** (from its moments) × **freshness** (long since last brought up) × **respect** (ignored twice: rests longer).
The top ones are brought up, still at most 3 a day, spaced, never during a live game. A feature comes back when its
need comes back, after a rest period (e.g. 14 days), never as nagging.

### 4. The coverage checks (for us)
A test fails if any feature has no moment, no story reason, no page, or reads data nothing else uses. The UI check and
the weekly memo show: features never used by the player, features ignored, features that helped most.

### 5. The data map
Every data file the app keeps is listed with the features that use it. A data file nobody uses = a feature to
connect or data to stop collecting.

## Order of building (one thing at a time, each tested)
1. ✅ **Done 28 Nov:** the feature map (`coach/features.py`, 24 features) + `tests/test_features.py` (every page,
   tour item, suggestion kind and data file is mapped; each check proven by breaking the map on purpose). No change
   in behaviour. **It found 8 gaps, not 4:** Practice, Your plan, Your level, the weekly report, Game of the month,
   Wrapped, Blindfold and Guess the move are only ever brought up by the tour. Every data file is used by something.
2. ✅ **Done 28 Nov (with step 3's main part):** the use record (per feature: times brought up and opened, last
   dates, in nudges.json) and the return rule in coach/nudge.py: a suggestion from the player's data rests 21 days
   after it was opened, or after 2 days shown without being opened, then comes back if the need is still there.
   Tour introductions: 2 days, a rest, 4 tries in all, then only data moments (they used to repeat forever).
   Players updating start gradually (pages opened before count as opened on the first day).
   **60 days simulated on the owner's real data:** old rule: 2 data suggestions in 60 days (everything was opened
   once, so the coaches went quiet) and 5 tour lines nagging until stopped; new rule: 21 data suggestions (rematch,
   clock drill, lesson, endgames, every ~3 weeks), 36 of 60 days with something, quiet days between.
   tests/test_nudge_returns.py.
3. Still to do in the picker: score the need (how strongly the data shows it), not only yes/no, and prefer the
   feature that helped this player before (from the use record).
4. ✅ **Done 28 Nov (storyline step 3.1 + 3.2): no gaps left** (`features.GAPS == []`). Your level: a new rank
   (Viktor, with the notebook page). Practice: 3+ positions due again today and none practised yet (Maya).
   Weekly report: Sunday, after a week with 3+ games (Viktor's letter). Game of the month: days 1–3 of a month, the
   month's best win (Maya, names the opponent). Wrapped: days 1–3, 5+ games in the month (Viktor). Blindfold: once
   you're a Club player (Viktor, his Berlin boyhood). Guess the move: 4+ moves in your last 10 games that walked
   into a fork, trick or mate they had planned, and this week's challenge not tried (Maya). Your plan already had
   one the map had missed: Home's "Something new for you" when plan.py picks a new card (`features.SPOKEN`).
   Lines in Viktor's own first person (rank, Blindfold, letter, Wrapped) are said by Viktor even on Maya's page.
   Checked on the owner's data: on Sunday 29 Nov practice (5 due), the letter (14 games) and Blindfold would come;
   on 1 Dec also the film (best win against korashy77) and Wrapped (15 games). tests/test_right_time.py.
5. Coverage in the weekly memo.
Every new feature from then on (the Book, analysis board, master games, Centaur) is added to the map first.
