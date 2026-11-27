# Fair-play audit of Knightwise (27 Nov 2026)

**The rule:** during any game against a real person, Knightwise is completely off: no hints, no arrows, no voice, no
reading the board. Everywhere else it is on.

**Why:** every player must be able to trust that the extension can never act in a live game, so every path was
traced and checked.

**How it was checked:** every content script, message and app endpoint the extension uses was read line by line.
Each risky situation is also run as a test: `tests/test_fair_play.py` loads the extension's real page scripts into a
small stand-in for a chess.com tab (`tests/fair_play_page.js`) and checks what appears, what is drawn and what is said.

**Not yet checked on the real chess.com site.** See "What the owner must check" at the end.

## The short answer

Before this audit there were **four real risks**. All four are fixed on branch `claude/stabilise-after-1-2-e3103b`
(not in 1.2, which is released from `dev-0.6`):

| # | Risk | Before | Now |
|---|------|--------|-----|
| 1 | A new game on the same page as a finished one (a rematch, or a live game whose address looks like a finished game) | The old game's review stayed up. Its arrows came back whenever the new game reached a position from the old one, including the green "Better" engine arrow, and Maya said the move's line out loud | Nothing shows unless chess.com's move list on the page is exactly the finished game's length. A new game takes the review, the arrows and the voice away at once |
| 2 | A live game in one tab, Knightwise in another tab | Only the member-profile prep was blocked, and only for `/game/live` and `/play/online`. chess.com moved live games to `/game/<id>` on 13 Oct, so in practice nothing was blocked. A finished game's review (same opening: the same "Better" arrow), Ask, Talk and the warm-up all worked next to a live game | Every chess.com tab marks itself "a game may be running here" until the review has confirmed a finished game. While any other tab has that mark, the coach, Ask, Talk, the red ring, the warm-up and the review all stay off |
| 3 | A late answer, after going into a game | An answer to Ask (or the warm-up, or the red ring's next step on a timer) that came back after the player had clicked into a game opened Maya's box on the game page and spoke the answer | Everything is checked at the moment it would show or speak: still the same coach page, and no live game elsewhere. Otherwise nothing |
| 4 | Knightwise updating itself during a game | The extension reloads itself when the app brings new files. A reload forgets which tabs hold games, and the old script in that tab can't say so again, so other tabs would have come back on | The reload waits while any tab may hold a game. The cross-tab mark also lives in chess.com's own page storage, which still works in a tab whose Knightwise was updated underneath it |

One smaller fix: the self-check on unknown pages could, if chess.com renamed its board, look at every piece's position
to find the board. On a page that isn't a review it now looks for the board **by name only**, never at the pieces.

## Every path, one by one

"Safe" means the path can't show, draw, say or read anything during a live game. File:line refers to this branch.

### Where the extension runs at all

| Path | Verdict | Evidence |
|------|---------|----------|
| The extension only runs on `https://www.chess.com/*`, top frame only, and only talks to the app on this PC | Safe | `extension/manifest.json:12-19`; `extension/coach.js:9`; `extension/buddy.js:7` |
| The app only answers its own window and the Knightwise extension (other sites are refused) | Safe | `coach/service.py:265` |

### The review on the game page (`coach.js`): arrows, Maya's review box, her voice

| Path | Verdict | Evidence |
|------|---------|----------|
| A live game at any address (`/game/<id>`, `/game/live/<id>`, `/live/game/<id>`, `/game/daily/<id>`) | Safe | The app answers `known: false` with no moments, no players, nothing, for any game that isn't in chess.com's public archive of **finished** games (`coach/service.py:283`; the app only downloads the monthly archives, `coach/fetch.py:41`). With no moments, `draw()` stops at its first line and nothing is read from the page |
| A finished-looking address that is really a live game (chess.com can use the same address for both) | Safe | Same as above: what decides is the archive, not the address |
| A rematch or new game starting on the same page as a finished, reviewed game | **Was a risk, fixed** | The app now sends the finished game's number of half-moves (`coach/service.py:291`). The review shows only while chess.com's move list has exactly that many (`extension/contract.js:157`, `extension/coach.js:53`); otherwise everything goes, voice included (`extension/coach.js:59`, `:67`, `:294`). Test: `test_a_new_game_on_the_same_page_takes_the_review_away` |
| The page never shows the finished game's move list | Safe (fixed in passing) | Nothing is shown or said at all. Test: `test_nothing_without_the_finished_games_move_list` |
| A finished game's review while a live game is on in another tab | **Was a risk, fixed** | `extension/coach.js:53` (`liveElsewhere`), `:303`. Test: `test_no_review_while_a_game_is_on_in_another_tab` |
| The review's step buttons click chess.com's move list | Safe | Only from Maya's review box, which only exists when the checks above pass |
| Waiting for a just-finished game (asks the app every 20 s for 15 minutes) | Safe | It only asks for the game number; nothing is read from the board while waiting (`extension/coach.js:218-245`) |

### Maya and Viktor on chess.com (`buddy.js`): the coach box, Ask, Talk, warm-up, badges, red ring

| Path | Verdict | Evidence |
|------|---------|----------|
| Which pages the coach appears on | Safe | Only an allow-list: home, puzzles (not Puzzle Battle), lessons, the games archive, stats, a member profile (`extension/buddy.js:10`). Every game and play page gets nothing |
| A late answer to Ask, Talk or the warm-up after going into a game | **Was a risk, fixed** | One check at the moment anything shows or speaks (`extension/buddy.js:25`, `:64`; the voice in `speak()`). Test: `test_a_late_answer_never_appears_on_a_game_page` |
| The coach while a live game is on in another tab | **Was a risk, fixed** | `extension/buddy.js:546` (no coach, not even a request to the app), `:624` (she goes within about a second if a game starts elsewhere, and comes back when it ends). Tests: `test_no_coach_while_a_game_is_on_in_another_tab`, `test_the_coach_goes_when_a_game_starts_in_another_tab` |
| Prep against a player (member profile) while a game is on | **Was a risk, fixed** | The old check knew only `/game/live` and `/play/online`; now every game address counts (`extension/contract.js:149`, sent at `extension/buddy.js:535`; the background still refuses at `extension/background.js:79`). Test: `test_every_game_address_counts_as_maybe_live` |
| Talk (the microphone) | Safe | Leaving the page stops it without sending (`extension/buddy.js:51`); the tab closing or loading another page stops it (`extension/background.js:62`, `:64`); folding the box stops it; at most one minute (`extension/offscreen.js:68`) |
| The red ring (step-by-step guide) | **Was a small risk, fixed** | It reads links and buttons, never the board, and only on coach pages or chess.com's Play menu page with no clock on it (`extension/buddy.js:330`). Its next step runs on a timer, which could fire after the player had gone into a game; now it checks first (`extension/buddy.js:263`) |
| The warm-up | Safe | Only on chess.com's home page, positions from the player's own practice, never from the page (`extension/buddy.js:337`; `coach/service.py:348`) |
| Badge banner | Safe | Only on a coach page (`extension/buddy.js:470`) |
| The archive tags | Safe | Only on `/games/archive`, and the app only tags finished, checked games (`extension/buddy.js:595`; `coach/service.py:302`) |
| "Knightwise was updated, refresh" note | Safe (tightened) | Never on a game page now (`extension/buddy.js:37`) |
| The self-check on unknown pages (has chess.com moved its game pages?) | **Was a small risk, fixed** | Only the board's presence by name, never the pieces (`extension/contract.js:53`, `extension/buddy.js:539`) |
| Maya's tour | Safe | It is in the Knightwise app window only; nothing of it runs on chess.com |

### The background, the voice player, the toolbar popup

| Path | Verdict | Evidence |
|------|---------|----------|
| The voice (offscreen player) | Safe | It only plays what a page script asks for; every page script now checks before asking (`extension/background.js:141`) |
| The extension reloading itself for an update | **Was a risk, fixed** | Waits while any tab may hold a game (`extension/background.js:30`) |
| The toolbar popup | Safe | Only the app's status and two links to the app (`extension/popup.js:5`) |

### The app endpoints the extension calls

| Endpoint | Verdict | Why |
|----------|---------|-----|
| `/api/game/<id>` | Safe | Unknown (not finished and archived) games get nothing (`coach/service.py:283`) |
| `/api/coach` | Safe | A game it doesn't know gets no board facts (`coach_says` in `coach/service.py`) |
| `/api/tags` | Safe | Finished, checked games only |
| `/api/talk`, `/api/chat` | Safe from the extension | Only called from coach pages, which are now off while a game may be running anywhere. They never receive the board |
| `/api/warmup`, `/api/practice` | Safe | The player's own practice positions |
| `/api/say`, `/api/listen` | Safe | Voice in and out; only used by the checked page scripts |
| `/api/try/<game>/<ply>`, `/api/rematch/...` | Safe | Checked, finished games only (`coach/service.py:561`) |
| `/api/check-now`, `/api/health`, `/api/hello`, `/api/fixes`, `/api/extension-stamp`, `/api/show`, `/api/badges/shown` | Safe | No chess content |

## What stays, and why (honest limits)

1. **About 0.7 seconds after changing page.** chess.com changes pages without reloading; the coach notices within
   0.7 s (the review within 0.15 s). In that moment a box that was already open (plain text, no board) can still be
   on screen. Nothing new can appear or be said in that time (every show is checked at the moment it happens).
2. **The Knightwise app window itself.** A person can open the Knightwise app during a game and use its review, Ask,
   the engine on a position they set up, or Prep. The extension can't stop a person using their own app. *Owner
   decision:* the extension already knows when a game may be running; it could tell the app, and the app could pause
   its engine and AI features until the game ends.
3. **Bot games count as "may be live".** `/game/computer` and `/play/computer` are treated like real games, so the
   coach in other tabs is quiet during a bot game too. Safe, maybe stricter than needed. *Owner decision* whether bots
   should be excluded.
4. **Daily (correspondence) games.** An open daily game page counts as live. A daily game that is running but not open
   in any tab can't be seen, so Prep against that opponent works then. Knightwise never reads an unfinished daily game
   (the archives only hold finished games). chess.com allows opening databases in daily games but not engines; *owner
   decision* whether Prep (which uses the engine for "how to beat them") should be off while the player has any
   daily game going (it would need the player's ongoing games from chess.com's public API).
5. **Fail-safe side effects.** If chess.com's page storage can't be read, the coach stays off everywhere. A tab that
   crashed keeps the others quiet for up to 150 s. If chess.com renames its move list, the review shows nothing and the
   self-check says "move-list".

## What the owner must check by hand (after the exams)

On the real chess.com, in their own Chrome, with the extension from this branch:

1. A finished game's review still appears (arrows, Maya, voice) and the step buttons still move the board.
2. In a second tab, open chess.com home: Maya appears. Then start a game (a bot game is enough) in the first tab:
   within a second Maya goes from the home tab; finish the game and she comes back.
3. After a finished game, press chess.com's Rematch on the game page: the review must vanish the moment the new game
   starts, whatever the address shows.
