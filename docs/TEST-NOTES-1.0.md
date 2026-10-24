# Hand test 1.0: what the owner found (22 Oct)

Written down as we go, so nothing is lost. The owner's own full notes come at the end of the test.
Each one: what was seen, then the fix.

## Session 0: the first start
1. **The first start's puzzle download took 10 minutes, with no progress** (300 MB streamed at 0.5 MB/s; the bar sat
   near empty on "Downloading puzzles…"). Fix: pack the kept set (31 themes, 27,577 puzzles, 6.2 MB, version 4,
   saved from this test) in the Store package; if it ever downloads, show real progress.
2. **The build packs 225 MB of trailer files** (`coach/ui/vendor/trailer`, the trailer songs) that players don't need.
   Fix: leave them out of `installer/Knightwise.spec`. Owner: "keep everything relevant packed in the Store package".
3. **Home shows zeros while checking** ("0 games checked", "0 won · 0 drawn · 0 lost"). Fix: "Checking your games:
   56 of 145…" until done.
4. **The Home help card** ("Your coach's summary: the habit…") may be too much text. Owner's call.
5. **Home didn't redraw when the check finished** (opened from the Store icon mid-check), and clicking Home while on
   Home does nothing. Fix: the page redraws when the phase turns ready; clicking the current page reloads it.
   (Opening the Store icon showed the running 0.6 test copy: that part worked as designed.)
6. **Your focus card: the "Before every move, ask…" line is unnecessary.** Fix: drop it from the card.
7. **The sidebar's "Voice on" button was unclear** ("what is voice on voice off"). Owner: remove it, Settings has it.
   Fix: take the button out of the sidebar (and its code); the voice stays in Settings.
8. **Settings: pressing Save key jumps the page back to the top.** Fix: keep the place (redraw the key row only, or
   restore the scroll), and show "Saved" right by the button.
9. **"Talking is on… Your Groq or Gemini key hears you"** names two companies, and the key guide recommends Groq:
   subjective. Owner: neutral words; the "(free)" note already there is enough; then "remove this line too".
   Fix: no "Talking is on" line at all, and a guide that lists the keys without a favourite.
   **Hearing, checked for every provider the app takes** (owner: "mention the voice thing after checking other
   providers"): Groq and Gemini hear today; **OpenAI can too** (its speech-to-text, the same request shape as Groq's:
   add it, `gpt-4o-mini-transcribe`); **Claude can't** (Anthropic has no speech-to-text). So after the fix three of the
   four hear. Settings says it once, plainly, next to the keys: "Talking works with a Groq, Gemini or OpenAI key;
   a Claude key answers in writing." No favourite; the "No key" message (ai.hear) gets the same words.
10. **The app can't tell which extension version is connected.** Chrome still had 0.5.0 from before the test.
    Fix: the extension sends its version; Settings shows it and warns when it's older than the app.
11. **Settings still said "connected" after the extension was removed.** It only checks that the extension was
    seen once (`extension_in` timestamps), never how long ago; the extension checks in every minute. Fix: connected
    only if seen in the last 3 minutes; otherwise "not connected: last seen 00:07".

12. **"Good morning" at midnight on Home, "Good evening" from Maya.** Two rules for after midnight. Fix: one rule,
    evening until 5 am.
13. **Talking: she said "Sure" and did nothing** (the owner's five requests: review a game, open settings…). Hearing
    was perfect (all five heard word for word). The AI wrote its orders in shapes the app threw away, made up a game
    id for "third last", and fell back to a stock habit line. **Fixed 22 Oct (talk.py):** a flat answer
    {do, what, say}; games numbered (1 = the last); any shape the AI writes is read, still checked; one retry told
    what was wrong; a refused order is never promised; busy keys are said plainly. Measured with
    `installer/talk_eval.py` (30 real phrasings, the real AI): before, 1 of 5; after, at a person's pace, actions
    16/18 (one "fail" was "go home" on Home), off-topic 11/12 (weather, homework, poems, "you're useless": a kind
    redirect, nothing opened), 0 unanswered. Left: "I'm playing X next, help me prepare" sometimes isn't prep;
    "delete all my games" opens Settings. Free keys allow about 4 turns a minute with all the facts: fewer games
    sent (12) to stretch it.

14. (see "Done during the test")
15. **The coaches greet unpredictably** (owner: sometimes twice, sometimes on every tab, sometimes silent until the
    face is clicked, sometimes the coach switches without a word; e.g. Learn it on Home opened Your plan and Viktor
    showed "Good, you're back…" without speaking). Cause: two things race when a page opens: `Coach.arrive` (the
    section greeting: spoken only on the first visit today, silent after) and the page's own `Coach.react` line
    (spoken every time); whichever lands last wins. Fix: one rule, the coach speaks exactly once per page opened
    (the greeting the first time today, else the page's line), never twice, never silent. Owner's detailed notes to come.
16. **Talking: "what was my first ever game?"** She only knows the last 12 games. Fix: give her the record's
    totals and first game, or say plainly she sees the last 12.
17. **Talking: Maya opened Viktor's page and Viktor never came.** Fixed 22 Oct: a handover; the page's coach takes
    over, speaks, and the next Talk is with them (the conversation carries over).
18. **Report it did nothing** (the global feedbackBox called itself). Fixed 22 Oct.

19. **Practice always opened on the same game (vs Geethasharvesh).** No answers had been saved in the test copy, so
    the same "clearest first" positions led every visit. Fixed 22 Oct: new positions come in a different order each
    day (the same all day). To check: whether answers are being saved at all (no practice.jsonl yet).
20. **Talking: "Who made this app? What can Viktor do?"** Maya called Viktor "the avatar" and didn't know the maker.
    Fix: give the coaches a few facts about Knightwise (made by Abhra Chakraborty, free; Maya: games, practice;
    Viktor: progress, plan) and what they can do by voice.

21. **Game review had no start and the coach didn't follow ◀ ▶** (everything on screen at once; Maya silent on
    Next/Previous; "tap the game and choose Review" for a button that didn't exist; a clean game had nothing to
    review). Fixed 22 Oct: ▶ Start review (nothing walks or talks before it); ◀ ▶ under the board drive the review and
    Maya says every step, going back says it again; three ways: Key moments, Highlights (a clean game) and Whole game,
    move by move: who moved which piece from where, what it attacks or leaves loose, the engine's verdict on your
    moves and their slips (coach/narrate.py, no AI); "next", "back" and "start the review" by voice. The AI only for
    wording later, never for the chess (owner: "if our engine is more accurate should we use AI?").

22. **The look feels "AI-made" and too busy** (owner, 22 Oct): the coloured bar on a card's left edge ("every AI
    tool has it, I hate it"); too many colours competing so nothing can be focused on; too much text on Home and the
    review; borders too sharp. Chess.com as the bar: easy to navigate, colour placed with care, softer shapes. Not
    fewer features, a calmer way of showing them. Plan: no left bars (10 places in app.css); cards set apart by
    shade and soft corners; one accent (the board green) for the one main action, red only for danger; warm neutral
    greys; one title and one short line per card, details on demand or spoken; a clear first thing on each page.
    Home first (mockup first), then the review, then the rest.

23. **(Fixed 22 Oct: Maya's face, a clear field, mic and send inside, three questions to tap on Home and in the review.)** **The Ask bar feels underrated and doesn't look like a place to type** (Home and the review). Fix later: a
    clear input look (a search icon or the coach's face on the left, a visible field, the mic as an icon), the
    Talk and Ask buttons as icons inside the bar, a warmer placeholder.

24. **On chess.com, "can't draw the arrows here" stuck after chess.com disconnected and reconnected** (its board
    was empty for over 20 s). Fixed 22 Oct: the extension keeps looking and draws once the pieces come back.
25. **Whisper "heard" "Subtitles by the Amara.org community" in near silence** and Maya answered it. Fixed 22 Oct:
    near-silent recordings aren't sent; parts Whisper scores as no speech are dropped.
26. **The review's key moment was a wall of text and its buttons overflowed.** Fixed 22 Oct: chips for the steps,
    one line of how hard, short wrapping buttons; the rest on hover or spoken. The chess.com panel needs the same.
27. **Maya too fast when teaching.** Fixed 22 Oct: a slower pace for reviews, training and numbers.

28. **The rating tile shows only rapid** (293), so after a blitz game at 100 the owner thought they "fell to 100".
    Fix: one line per game type played (Rapid 293 · Blitz 100), each with its 30-day change.

29. **Review: on the opponent's blunder, a green "Better" arrow showed the player's next move** (Qxe5+ vs Laro1966),
    which they then played. Fixed 22 Oct: if you took the chance, their move says "a blunder by them" and yours
    "you punished their mistake"; an arrow only for a chance you missed, labelled "Your chance". Audit of 40 games:
    "Qxg2# wins something" now "is checkmate"; a king move no longer "wins something"; queen checks "attacked" by
    the king were called Brilliant (kings only count against an undefended piece; a fair trade is never a sacrifice).

30. **"So many Excellent moves, was it real?"** In a decided game the win chance barely moves, so moves that gave away
    a pawn or more looked Excellent. Fixed 22 Oct: a pawn or more given away is at most Good, two or more an
    Inaccuracy (your moves in 40 games: 1,313 Excellent before, 308 after). Left: accuracy (94.7 vs Laro1966) still
    uses the win-chance scale only, like chess.com and Lichess, so it runs high in one-sided games: look at it later.
    Qxa8 vs Laro1966 checked: a real blunder (+8.8 to 0.0, a perpetual check).

31. **Talking in a review:** "Next." was refused (the AI wrote next with a word after it: fixed, any shape works);
    "Whole game, previous move." got "I can't show or change anything" (fixed in the instructions: moving through a
    review is always allowed). Worked: next, back, "previous move", "Back. Sorry, next.", and a long back/next tangle.

32. **Rematch: unclear where it starts, and the human-move model over-explained.** Fixed 22 Oct: "▶ Starts here: move
    26, you to move" at the top of the moves; a short header; the opponent as a player card ("Laro1966-style 537 ·
    Plays like real 537 players"), the Maia explanation on hover.

33. **chess.com talking:** "How do I play a bot?" opened Knightwise's Practice ("choose a bot there": there are none).
    Fixed 22 Oct (instructions: on chess.com, going somewhere on chess.com is the red ring; Knightwise has no bots);
    measured: bots, puzzles and "my old games" all guide, "open my plan" still opens the app. Left: "please do" after
    the coach's offer did nothing; a yes should do what was just offered.
34. **chess.com panel:** the coach now follows chess.com's own move buttons (each move's line, arrows, voice) and the
    panel can be scrolled; the key moment as chips (fixed 22 Oct). Repeat visits: a folded tab, the first page of each
    visit opens and talks; with buttons all the text shows (fixed).

35. **Chrome lists a warning under the extension's Errors:** "ScriptProcessorNode is deprecated" (offscreen.js, the
    chess.com microphone). It works; Chrome hasn't removed it. After launch: move the recorder to an AudioWorklet.

Also asked: Home after the newest 20 games, the rest checked in the background (offered, not yet decided).

## Done during the test (22 Oct)
- 13, talking: fixed and measured (above).
- 14, the owner: "we need to say that AI can make mistakes, report issues to my email". Every AI answer (the coach's
  bubble after Talk, the Ask boxes on Home and in a review) now ends with a small "AI can make mistakes. Report it";
  Report it opens the feedback box, which emails FEEDBACK_TO. The chess.com bubble (extension/buddy.js) still needs it.
- Feedback, the owner: "as easy as just a send button". One-click Send through Web3Forms (free, 250 a month; key in
  coach/feedback.key, packed, never in the repo), at most 4 a day per PC, an optional "your email, if you'd like a
  reply" (reply-to), no Copy text button. Auto-replies are a paid Web3Forms feature: the owner replies by hand for
  now and may set up a free Gmail Apps Script auto-reply later.
- 22, the look (the owner approved a Home mockup, then "work on every UI change that's needed"): warm layered greys,
  no left bars, soft cards, pressable buttons, one green per screen, coloured sidebar icons and four small status
  icons (finding 7: no Voice button). Home, Practice, Plan, Level, Course, Progress, Settings (finding 8: keeps its
  place; finding 9: no line naming companies), Games, the review, Prep, endgames, repertoire and the opening tree
  redrawn as pictures, numbers and bars; long page intros fold into a ? by the title everywhere (finding 4); the
  coach's bubble shows two sentences and one button, More for the rest, in the app and on chess.com, where AI answers
  now say "AI can make mistakes · Report it" (finding 14). The extension needs a reload in Chrome to show it.

## Where we stopped (22 Oct, 01:05)
Session 0 done; Session A: A1 done (A1.3 checked from the record; A1.4 is the button being removed), next is **A2.1
Practice**. Then A3–A8, Session B (on chess.com, with the 0.6 extension now loaded), Session C (voice). Restart with
`try test` (not `test new`): the data and keys are kept.

## 23 Oct: where the test stopped (low usage)
- 36. The coach's typed answer never went away (Home and every Ask bar). Fixed: it fades after 90 s unless the mouse is on it. **Check it.**
- 37. The red ring stopped on a repeat-visit page (the quiet tab ran first). Fixed in a286983. **Recheck: chess.com home → puzzles button → ring on Puzzles, then on Solve Puzzles.**
- Still to do in the chess.com section: Maya stays away on the Play page (fair play).
- Then in this order: Talking (including "please do" after an offer), Practice and daily, Plan/Course/Level, Train, Home/Progress/Settings, rare things.
- Open fixes: 28 (rating per game type), accuracy runs high in one-sided games, "please do".
- After the test (not before): rebuild with PyInstaller, then make_msix.py, then a smoke test, then upload with a parent.
- 38. Maya brings up the habit in small talk ("hailo" -> "keep focusing on safe piece play"). Check in the Talking section.

## 23 Oct: launch postponed
The owner called off the same-day launch. The test goes on in order next session (above); build only after it.

## 23 Oct: the number check (tools/number_check.py)
Every statistic recounted from the raw files (only one move's label borrowed) and compared with the app: 482 match.
- 39. Home's graph ended on a part-window (3 games, 0.67) next to "0.7 in your last 20". Fixed: full windows counted back from the newest game.
- 40. "Missed a free capture" was said of 5 in 25 pieces that weren't free (a trade or a tactic). Fixed: only when the capture wins 2+ after every recapture (static exchange).
- "Left a piece hanging": 24 of 25 really lose material at once (the odd one is a quiet move the engine's line punishes later).
- Level and course: 24 of 24 match (the teacher's reasons, mistakes of 10+ points, last 20 games).
- One game unchecked: resigned before move 1 (right).
- Open: Home's hanging tile (big mistakes only, 0.45 a game) and Level's "Keep every piece safe" (every mistake of 10+, 0.4) measure one skill two ways.
- Fresh: new games every 5 minutes, at once when a finished game is opened on chess.com; open pages of numbers redraw when new games are checked.
- 41. Puzzles in lessons and the plan could repeat ones already solved; today's 5 minutes picked your own position at random (could repeat). Fixed: anything answered on an earlier day is never offered again while there are new ones. Checked: tomorrow's set shares nothing with today's answers. Progress is saved (practice.jsonl, 10 answers today) and badges count from it.
- 42. Today's 5 minutes changed mid-day after a restart or new games (its position came from the rebuilt practice list). Fixed: the day's set is kept as first made until midnight.

- 43 (23 Oct, daily): "Back home" button showed on Home after finishing Today's 5 minutes; an opening question got a Practice offer. Fixed: no button when already home; opening questions offer the opening tree.
- 44 (23 Oct, plan): the opening's explanations only flashed in the bubble, and a finished page had no clear way back. Fixed: each move's why stays on the page; every finished set shows a green "Back to …" button. (The Italian card turning into Four Knights was correct: it was done, and the next opening took its place.)
- 45 (23 Oct, plan): no way to tell how many topics there are or what comes next; finished topics couldn't be played again; leaving a set halfway lost its answers; the round arrow (bottom left) did nothing. Fixed: each card shows "Topic n of N · next: …"; a finished card moves down to Done (as a card, to play again) and the next topic takes its place; a tally says how many now, done and to come; every set remembers today's answers; the arrow checks for new games and reloads.
- 46 (23 Oct, plan, owner's idea): "it's like a book... practise everything, curated". Built: a visible top line; the roads now run through the whole Lichess library (26 tactics, 5 endings, endless openings); Explore searches or browses every theme and all 3,160 catalogue opening lines (140 families), as White or Black, in three dropdowns (Tactics, Endings, Openings → family → lines). Checked: all 31 themes build, 1,100 sampled opening lines build from both sides, 0 failures.
- 47 (23 Oct, lessons): no way to ask while learning. Built: the ask box on every learning page, grounded in Stockfish's facts for that exact position and the lesson's own words. While still solving, the engine's moves are held back from the AI, so it can't give the answer away; the hint follows the line's own idea. Checked with three real questions: no move named while solving.
- 48 (23 Oct, plan): started sets needed a bar and an In progress place. Built: a set answered part-way is kept on the computer with its own positions; top cards show the bar and Continue; Explore picks go to In progress; finishing anything moves it to Done. Checked end to end in the browser (Explore pick: start → leave → In progress 1 of 4 → continue at 2 → finish → Done; top card: bar + Continue). Bug found and fixed on the way: the server refused saves over 10 KB.
- 49 (23 Oct): Home's week bar looked "filled at the end" with no meaning: each day now has its letter, today's in white, a hover says done or not. Your plan: one header line (no tally); order is cards, In progress, Explore, Done at the bottom.
- 50 (23 Oct, Home): the green button vanished once the 5 minutes were done. Now it moves to the first card not done today: Today's 5 minutes → the latest game's review (opened) → the focus (5+ positions practised outside the 5 minutes); all done, all grey; after midnight it starts again from the 5 minutes (`today_done()` in service.py).
- 51 (23 Oct, course): "← The lesson" did nothing. Cause: pages that swap their content in place (a lesson's practice, a finished set) keep the same address, and a link to the current address never fires. Fixed app-wide: go() and every in-app link to the page you're on draw it again.
- 52 (23 Oct, level): "confusing". A dot was a mistake (rounded to "per 10 games"), not a game, and red dots read like progress. Now: exact counts over the last 20 games against the aim ("8 in your last 20 games · aim 6 or fewer"), a bar (green up to the aim, red past it, a white mark for you), Done or "2 too many", and "1 of 5 done → all 5: Level 2".
- 53 (23 Oct, level, second pass): the bar's scale stretched per card (the mark always sat in the same place), sentences still crowded the cards, and later levels couldn't be seen. Now: one big number per card (red over, green done) against "aim ≤ n", Done or "n too many", words on hover; click any level to see its cards with today's numbers.
- 53 (23 Oct, level, second pass): the bar's scale stretched per card (the mark always sat in the same place), sentences crowded the cards, later levels couldn't be seen. Now: one big number per card (red over, green done) against "aim ≤ n", Done or "n too many", words on hover; click any level to see its cards with today's numbers; cards with something to do first, done ones at the bottom.
- 54 (23 Oct, level ↔ course): a Level card whose lesson was already learnt looked untouched. Now it says "Learnt · watching your next games", its button reads "Learn again", and the green button goes to the next thing not yet done. (Progress is saved by each page itself, however it was opened: practice, lessons, endgames, plan sets.)
- 55 (23 Oct, owner's idea): a user who only reviews games would never find most of the app. Built: the tour. Maya and Viktor bring every feature (20 of them), up to 3 new things a day, 20 minutes apart, never two suggestions together, never one already opened; the ring follows the path into the page (Train → Blindfold tile; Your plan → the Explore bar, the Done area). Checked live: Maya's first one on Home, Viktor's Blindfold on Train, the Done area ringed and scrolled to.
- 56 (23 Oct, report/PDF): "wrong and empty mostly". Wrong: "Rating 293 to 100 (-193)" mixed rapid and blitz (finding 28 again); "Best game" was a loss. Fixed: a rating per kind of game, each from your last game of that kind before the period (week: blitz 155→100, rapid 311→293; month: rapid 254→293, matching Home's +39; checked against the raw files: the 29 May 100 was King of the Hill, not standard); the best game is a win or a draw, or not shown. Empty: a week with 2 games; the report now says so at the top and points to the month view. "Big mistakes" relabelled with its meaning on hover.
- 57 (23 Oct, film): "Save as a video" removed; music on by default every time; switching music on/off no longer restarts the film (it mutes in place, `stop.mute()`); the music comes in after about a second (MUSIC_WAIT 12 → 1; the song starts further in so its main part still lands on the first winning move).
- 58 (23 Oct, report PDF): the printed report came out squeezed into the menu's 216 px column (the menu is hidden in print, so the page fell into its grid column), every word cut off, 5 near-empty pages. Fixed in the print styles; checked by printing with headless Edge and reading it back: 2 full pages, every word whole.
- 59 (23 Oct, notes): Home's "Hear it from Maya" button removed (Maya greets and talks by herself).
- 60 (23 Oct, tour): Maya suggested Blindfold and a ring showed on Your plan in the owner's window (the server sent the right target; not reproduced in time). Owner's rule: nothing we can't be sure of. App rings off (`KW_RINGS = false`); every suggestion now says where in words ("In Train, open Blindfold"); chess.com keeps its red ring.
- 61 (23 Oct, notes): the AI usage bar showed 32% used the next day: the provider's "left" figure was kept in memory while Knightwise ran overnight. It now carries its day and is dropped when the day changes. (Note 6, the review's "best move": already shows the opponent's real reply; no change.)
- 62 (23 Oct, badges): 30 new badges (50 in all), each true about your chess: Big moments (comeback, survivor, converter, endgame grinder, promotion, miniature, holding your own, underdog run), Accuracy (sharp game, masterclass, no blunders, engine eye, good starts), Clock (time keeper, cool head), Rating (climber, new heights), Openings (scholar, loyal, castle early), Training (endgame master, blindfold, mind reader, tactician, opening learner, thinker, graduate, level up, streak keeper, on target). Accuracy counts only moves played while the game was still open (a decided game made 81 of 101 games "80%+"; now 12). Levels set so Gold takes an ordinary player 1-2 months.
- 63 (23 Oct, badge pop-up): a badge completed (Gold) pops up once, in the middle of a calm page: the app's overview pages, or chess.com's home, puzzles, lessons, stats (never a game page). History counts quietly (owner's choice): the Golds already held were recorded without a pop-up. Shown in one place, never again in the other. Checked: Fork-proof popped up in the owner's app window.
- 64 (23 Oct, progress): Report and "Your month, Wrapped" showed the same facts. The Wrapped button is gone from Progress; Wrapped plays from inside Report ("Play it as Wrapped").
- 65 (23 Oct, badge pop-up, owner's design): not a dialog in the middle with everything blurred. Now a banner slides down at the top (nothing covered): the medal fills from silver to gold, a chime (made in code, three rising notes) and confetti; the close button appears when that's done; it leaves by itself 5 s later. Same banner on chess.com.
- 66 (23 Oct, badge banner, owner): a different colour and cartoon-like, more animated. Now teal-to-blue with a thick dark outline; it drops in with a bounce, the medal pops, spins from silver to gold, eight stars burst, the name pops; chunky outlined confetti; a yellow ring runs round the close button for the seconds it stays.
- 67 (23 Oct, security check): 25 attacks on the local server (docs/SECURITY-CHECK-1.0.md). Fixed: a JSON list body raised an error (now 400); the connection queue raised from 5 to 64 (a 600-request burst lost 12). Keys, storage and permissions are fine. Found: the old installed 0.4.1 (looser rules) took the port when the test copy stopped; uninstall it.
- 68 (23 Oct, chaos test): Gremlins.js on all 25 app pages: no crash or freeze; one bug (7 times): a page finishing late drew over the page you'd moved to (Today's 5 minutes, plan lessons, Train, Settings). Fixed in the router, the practice board and Settings; re-run clean. A real foreign website (example.com) couldn't reach the server at all.
- 69 (23 Oct, extra checks): pip-audit (the Python libraries): no known vulnerabilities. Bandit (the code): 0 high; 2 medium on SHA-1, used only for cache names, now marked as not for security; the other 18 flags checked and safe (local server, fixed commands). Accessibility (axe-core 4.10.2, 13 pages, light and dark): the 8 menu icons had no names for screen readers, the Settings fields had no labels, and some grey, green and red text was too faint (3.2-4.4, needs 4.5). All fixed; re-scan clean except two minor heading-order notes.
- 70 (24 Oct, badge banner check, owner): seen in the app (Progress) and on chess.com's home. One bug: asked on the Games list, the answer came after a game was opened and the banner showed over the game. Now it shows only if you're still on the same overview page; otherwise it waits for the next calm page. (After reloading the extension, an open chess.com tab needs F5: normal for Chrome.)
- 71 (24 Oct, owner's idea): Prep goes deeper, "How to beat them". Stockfish (depth 10) checks only their moves in their last 12 games of their main time class (about 10-20 s, with a progress bar), sorted by the same habits as your games: their weak spot (a number a game), where they go wrong (opening, middlegame, endgame; clock low; winning games let slip), the opening they score worst in, three tips, and Punish their mistakes: up to 5 real positions just after one of their big mistakes, every move scored like your practice. Tried on a real player: 0.5 pieces left hanging a game, 5 sound puzzles. Prep, Wrapped (voice on the last card only), Game of the month button, green chips, "chess dot com" spoken: owner's notes the same night. The tour gains Punish and Game of the month (22 tips, 3 a day at most).
- 72 (24 Oct, owner: "2 or 3 killer insights are missing; more games; more positions; more organised"): How to beat them now reads their last 30 games (main time class first) and up to 10 puzzles (2 a game). Killer insights, the strongest 3 shown: the opening line where they score worst, for each colour (it must cover 10% of their games with that colour; with Practise this line), their king (castle rarely or late), their clock (rushed big mistakes, or often short of time), after a loss (their score drops). Page order: killer insights, weak spot / where they go wrong / your plan, Practise against them (Punish and Spar together), then The details. The insights show as soon as the games are checked; the puzzles follow. Tried on sreerupdaw (two opening lines, 38% and 33%) and hikaru (a rushed-mistakes edge).
- 73 (24 Oct, owner): a 51st badge, Homework done (Training): look a player up in Prep, then win your very next game against them, however many days or other games later. Each prep is kept on this PC (data/preps.json, the last 500); each game counts once, however many times you prepped before it. Levels 1, 3, 10. Prep's practice box says so.
- 74 (24 Oct, owner): "Against RIP_Hansie it went wrong at move 16. Play it again from there?" came again and again (every day until opened; before and after midnight), with the page's "Learn it" button, which opened something else. Now every suggestion in the app has its own button (Play it again, Open the game, Start, Show me...), and one not opened stops after 2 days (the new game and Today's 5 minutes stay daily). Prep's practice: Punish with the Homework done medal beside it, Spar its own block; Punish's lines vary.
- 75 (24 Oct, Opening tree): asked "10 of my 37 losses come from this side when I'm Black, why?", Maya answered from general habits: she didn't know which line was on screen. Now the page tells her the line selected, and she gets facts from the games that went that way (score, the mistakes made in them, when the first big one usually comes, what opponents and you play next). Tried: 1. e4 Nf6 2. Nc3 (8 games, 31%): pieces left hanging, around move ten.
- 76 (24 Oct, owner: "your gameplay changes; how can three lines stay fixed?"): the repertoire is re-checked after 50 new games and a month (both). A line is out of date if you played it in under a third of the games where it could come up, or scored under 40% with it in 5 or more. Then Viktor suggests new lines (once, the 2-day rule) and the card says why; nothing changes by itself. Choosing new lines starts the count again.
- 77 (24 Oct, owner): Repertoire cards were confusing (underlined like links, colour squares like tick boxes, Viktor's "to move six"). Now: "You play White" / "You play Black, against 1. e4" with a pawn, the line's moves, and "Your three openings: one as White, two as Black. Practise each one until you can play its first moves without thinking." Spar's own tile in Train opened Prep anyway (a duplicate): removed; Spar stands out inside Prep (blue block); the tour's Spar tip points to Prep.
- 78 (24 Oct, In your head): at first glance it didn't say what it was; Viktor's line was confusing. Now a short line under the title (plan moves ahead without moving the pieces), the plan as numbered slots that fill as you click (1 Your move, 2 Their reply, 3 Your move), the clue marked as a clue, and Viktor: "This trains seeing ahead. The pieces stay still: click your move, their best reply, then your next move. Then press Check my line." Train's rows fill their width (the gap where Spar was).
- 79 (24 Oct, In your head): a puzzle solved came back after leaving the page. Today's answers are now kept in the app: it opens on the first one not done, a done one says so with its line, the count says "2 of 5 · 1 done today", and Next skips the done ones.
- 80 (24 Oct, owner: "what does an academy teach that we don't?"): three basics at the start of Your course: What pieces are worth (1, 3, 3, 5, 9; count before every capture; fair trades), Attack with your cheapest piece (and capture with the cheapest), The basic checkmates (queen, rook, two rooks, with the Endgames trainer). Each has Lichess puzzles to practise; nothing to measure in games, so done once studied. Master games: to discuss first.
- 81 (24 Oct, owner: "most players won't add a key; they mustn't get bored"): without an AI key the ask boxes were switched off (only "add a key"), and typed questions got 2 stock lines. Now they offer questions to tap, by page (Home: what to work on, how am I doing, why do I lose, my last game, my openings; a review: this move, where it turned; a lesson: a hint, what it teaches), each answered from the player's own numbers in several wordings, never the same twice in a row, with follow-ups. Typed words still need a key (no word patterns). The AI's answers to the owner, checked in the log: right but shallow and the same fact ten ways; one made up ("Gukesh is very careful").
