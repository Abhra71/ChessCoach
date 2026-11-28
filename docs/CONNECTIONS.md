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
1. The feature map for the features that exist today (no change in behaviour) + the coverage test.
2. The use record.
3. The picker, replacing "once opened, never again", tested on the owner's real games ("is this me?").
4. Moments for the four features that have none, with their story lines.
5. Coverage in the weekly memo.
Every new feature from then on (the Book, analysis board, master games, Centaur) is added to the map first.
