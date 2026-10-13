# 0.5.0 test session: findings

The session ran on 12 Oct 2026 from a fresh start, using `try.bat fresh`, with Claude guiding by voice.
These are Claude's notes. The user keeps their own list and will debrief at the end.
Fix everything here, from major to minor, before publishing 0.5.0.

## Status, 13 Oct
- **Done:**
  - Parts 1–8, including a real game: fair play passed, and the review only works on the old address (finding 0).
  - 8.3: the real data came back unchanged.
  - The user's debrief arrived as a 42-point PDF, merged at the end of this file. The user has 2 or 3 more points to add.
- **Not done:**
  - Part 9, the AI with a Groq key. It moves to the retest round after the fixes.
- **Watching chess.com:** Claude can't attach to the user's own Chrome tab. It watches with full-screen screenshots, using a script in the scratchpad that calls SetProcessDPIAware. Look only at whether a coach shows during a game, never at the position.

## Major
0. **Most important: no review on the page right after a game.**
   - The game, 13 Oct: 185261729330 against hemmehra0416, a loss by resignation.
   - During and after the game, chess.com shows `/game/<id>` and moves it to `/live/game/<id>`. Maya never appears there (checked for 30 s).
   - She only appears on the old `/game/live/<id>`, after about 25 s, with all 3 moments, and her panel sits under chess.com's ads.
   - The cause: [manifest.json:17](../extension/manifest.json) only matches `/game/live|daily/*`, and so does [coach.js:15](../extension/coach.js) `idFromUrl`.
   - The fix: also match `/game/*` and `/live/game/*`. This stays fair play, because the app answers only for archived, finished games.
   - Also check the 25 s wait.
   - **Fair play passed:** 58 screenshots from 18:19 to 18:31 show no coach during the game. The app checked the game at 18:34 and found 3 moments.
0b. **The "Reply" arrow shows the engine's best reply as if it happened**, found by the user.
   - The game: 185261729330, move 15, you played g6.
   - The arrow and the text say Bxa8 and "their reply wins material". In the game, the opponent castled, O-O, missing it, and you then played Rd8.
   - Label it "Their best reply", and add what really happened: "In the game they missed it: O-O."
   - The better move, O-O-O, was legal; the user wondered if it was a glitch. Consider saying "castle queenside, O-O-O" in words, since a beginner may not trust a king moving two squares.
   - Check the file letters on the flipped board, which run h to a.
1. **Bot games can never be reviewed.**
   - chess.com's archive shows 152 games and Knightwise has 142. The bot games from 10 Oct, against Samay, are missing.
   - The public API leaves out games against the computer.
   - `extension/coach.js` `idFromUrl` only matches `/game/live|daily/`.
   - TEST-SESSION.md 7.5 and 7.7 promise this, so the guide is wrong too.
2. **There's no way from chess.com to the app.**
   - Zara's only button that opens the app, "Learn it in Knightwise", shows only when there's something new ([coaches.py:171](../coach/coaches.py)).
   - Once the lesson is done, the bridge is gone. Always offer **Open Knightwise**.
3. **Today's 5 minutes didn't save as done.**
   - Daily habit stayed at 0, and there is no daily.json.
   - practice.jsonl has only the game position and the puzzle. The opening drill never counted as solved, so `onDone` and POST /api/daily/done never ran.
4. **The coaches on chess.com "appear but do nothing".**
   - Each coach greets only once a day on each page ([buddy.js:170-174](../extension/buddy.js)). After that, Arjun on Puzzles and Viktor on the archive stay folded and silent.
   - That memory lives in the extension, so a fresh app doesn't reset it.
   - Rethink: talk when there's something new, or give a short line on each visit.
5. **Knightwise closed by itself** on the welcome screen at the first fresh start. The log has no error.
   - It may have been the console window being closed, but this is not confirmed.
   - Its error output now goes to `%TEMP%\kw-fresh.log`.
6. **A position accepts too many moves as right.**
   - The position: game 147199025072 at ply 13, queen on b7, today's idea "trapping a piece".
   - 8 moves count as right: Qb5 +6.5, d4 +6.1, c3, Nf3, Nh3, Nc3, d3 +4.6 and Be2 +4.3. d3 allows ...Rb8, which traps the queen, and still gets "right".
   - Every good move gets the same "yes, that keeps you safe", with no explanation of the danger. Tighten the bar, explain the move you played, and warn when it allows a trap.

7. **The user, 13 Oct: maybe one coach instead of four.**
   - The guide's voice, af_heart, which is Maya's, "feels the optimum", and the other coaches' voices aren't as good.
   - Claude's take: one coach, Maya, everywhere. A real coach is one person who knows you, which fits flagship 2.
   - Decide after the test. It would replace the four-coach decision of 11 Oct.

## Minor
7. **Opening tree (4.7):**
   - It doesn't explain how to read it.
   - There's no board showing a move's position.
   - The user wants to come back to this after the session, for a reason they'll explain.
8. **Settings, Arrows on chess.com:** "Set up" always shows ([app.js:667](../coach/ui/app.js)), even when Connected. Show it only when not connected.
9. **The extension page's Edge tab says Connected** although the extension is only in Chrome. `extension_seen` isn't recorded per browser. Record the browser from User-Agent and say "Connected in Chrome".
10. **The What AI adds card** ([coaches.js:282-291](../coach/ui/coaches.js)):
    - Only ticks and crosses, with no text in the cells.
    - The Free column's "–" becomes a red ✗.
    - The row "The coaches explain each moment in their own words" becomes **"One-to-one conversation with your coach"**: ✗ for free and ✓ for + AI.
11. **Badges were checked against the raw games.**
    - Checkmater 11, Giant slayer 4, best streak 5 and All-rounder 4 all match.
    - Winner shows 56 against 57 real wins, Dark side 25 against 26, and Regular 140 against 142.
    - One gap is the King of the Hill game, which is fair to leave out. One more game isn't counted: find which.
12. **Save as picture:** the picture is good. Add **Share** to WhatsApp, X, Instagram and others.
13. **Placement:**
    - Zara and her bubble cover chess.com's third card on home.
    - Folded Arjun sits on chess.com's "Remove Ads" bar.

## Correct, as expected
- **Fair play:** in rated puzzles, Arjun gave no moves and no arrows.
- **Import:** a fresh import checked 141 games with no errors.
- **Practice:** answers were saved correctly, 6 with 3 right, and the Sharp badge says 3.
- **The user's verdict:** training from their own games is the best part, "quite flagship". See [FLAGSHIPS.md](FLAGSHIPS.md).

## How the user wants the session run
- One step at a time, not several at once.
- Speak each step, and write it in the chat too.

---

# The user's debrief, 13 Oct: 42 points

From the user's PDF, "Nightwise Full App Review / Debriefing". The numbers are the user's.
Their rule: a symptom isn't automatically the cause, so investigate the objective, configuration and data before deciding. The bar is firm, though: no wrong puzzles, no fake progress, no misleading labels.

## A. Truth and accuracy, the most important
- **41, 42 Review: real move or engine move.**
  - The arrow called Stockfish's move the opponent's reply. Same as finding 0b.
  - Rebuild every key moment from the game record first:
    - You played: the real move, with a grade from Best to Blunder.
    - Better: shown only if one exists. If your move was already the best, say so.
    - They replied: their real move, and its better alternative if it was inaccurate.
- **33 One right move, two at most.** Accept a second only when it's genuinely correct. Same as finding 6, the position with 8 accepted moves.
- **24 "Winning with the Queen" lesson.**
  - The user thought the goal was checkmate. After 2 or 3 moves their queen was taken, the game ended, it was marked correct, and there was no confetti.
  - Investigate the objective, the label and the accepted line. Nothing incomplete may ship.
- **26, 29, 28 Right-first-time counts are inflated.**
  - The screens disagreed: "3 of 4", "4 right first time", Viktor's "All done, 4 of 4" with one still left, and "5 right first time" after 4 puzzles, then 6 after repeats.
  - Count unique puzzles, each once at most, and only if solved on the first try. The dots, totals, messages and badges must all use the same count.
- **31 "Listening is on" in Voice Settings** although no key is set. Show the real state.
- **37 AI-key nudges** ("Want real replies?…") must disappear when a valid key exists, and come back if it's removed. Use the live configuration, never a stale flag.
- **2 The voice picker.** Check that the picked voice is the one that actually speaks: the picker, the saved setting and playback must agree.

## B. Progress and practice that persists
- **14 Progress wiped when switching tabs**, in Today's 5 minutes, Practice and others. It must survive navigating away.
- **15, 9, 28 Practice should refresh daily without repeats.**
  - Attempted positions must not come back as new. Check whether there's a shortage of suitable positions.
  - Keep it varied, from the same game or others, and still curated.
- **7 No end state for Today's 5 minutes.** Next looped back to puzzle 1, with no celebration and no "done". Ties in with finding 3: the done-save never ran.
- **20 Keep:** the confetti after a correct Try it again worked well.
- **16, 30 Badges.**
  - Separate badges from chess.com games and badges from Knightwise practice; don't blend them misleadingly.
  - Add a colour legend for Bronze, Silver and Gold at the top right.
  - Make it clear which badges are complete. 17 of 21 felt too easy.
  - Show progress, current level and full completion separately.

## C. Coaching quality
- **6 Hints that grow.** After about 3 or 4 wrong tries, give a small hint (the piece, the direction, the idea) without the answer. Don't repeat the same sound and line.
- **39 After a puzzle, Arjun said nothing.** Give feedback tied to that position: what the move achieved and the lesson for real games.
- **8 Say when something is new.** Explain the idea, which pieces, and how it's used in a real game.
- **5 Remove "Click a piece, then the square to move it to."** Keep the coaching line, for example "One of their pieces has no safe square at all. Attack it."
- **4 Show the opponent's last move** in Today's 5 minutes and in puzzles.
- **12 The briefing belongs in the coach's bubble.** Replace "Here's the situation. Read it, then press I'm ready" with the useful line itself. Not everything has to go there.
- **38 Recommend where to practise.** On buttons like Open in Knightwise, Open on chess.com and Practise here, the coach should say which one is best for this skill, out loud, and why.
- **40 Greetings.**
  - The full welcome comes on the first meaningful visit to a section each day.
  - Coming back the same day keeps continuity with no repeated welcome. A new day brings a new greeting, never a reset.
  - Ties in with finding 4: coaches seemed to "do nothing".
- **18 Maya in Game Review.**
  - She should welcome you as soon as a game opens, not only after you click a moment.
  - A short spoken briefing and a recommendation, then one key moment at a time. Show the total, but work on one.

## D. Less clutter, beginner first
- **1 Hear your briefing:** is it needed? Re-evaluate, including its voice.
- **4, 10 Today's 5 minutes and Practice.**
  - Keep the small Mindset tab on the right, above I'm ready. Remove the text above it, such as "It's the middle game, two pawns down".
  - "Rated 1428" is unclear: check where it comes from and whether it's correct for a 254 player.
- **10 The game tags.** Keep 3 or 4 at most, and drop Move 13 and Middle game.
  - Remove the labels below practice: "Your own positions", "The move before a big mistake", "Puzzles on the same habit".
- **11 Repeated titles:** "Your game vs X, Move 7, still the opening" repeats too much. Simplify.
- **17 Game review shows too much at once.** Reveal it step by step, one clear piece at a time, keeping everything available.
- **21 The opening tree** is confusing for a beginner (1. e4, 1... e5, the drop-downs). Explain the notation, how to move around it, and what it teaches. Same as finding 7.
- **23 Every major section needs a beginner introduction.**
- **22 Zara's pointing finger** seemed to point at the wrong option, and moved when she was minimised. Check it, or remove it.

## E. Board
- **3 Selecting pieces.**
  - Clicking the selected piece again doesn't hide its move dots.
  - Clicking another piece leaves the first piece's dots on the board.
- **25 Captures:** mark a piece you can capture with a grey ring, so captures stand apart from plain moves.

## F. Voice and speed
- **13, 19, 36 Slower:** Arjun, Maya and Zara all speak too fast for teaching.
  - The guide used af_heart at speed 1.0 and the user found it optimal, so compare the in-app speed with the guide's.
  - Relates to finding 7: one coach instead of four.
- **35 The pop-up on chess.com didn't open by itself, and the voice started late.** Check whether Chrome's rule needing a first click before audio is the cause, and handle it gracefully.
- **34** Find out whether the chess.com pop-up's voice needs the app running in the background. If it does, tell the user clearly.

## G. AI-key setup
- **32 Screenshots of the API-key setup**, for someone who has never made a key.

## The user's principles, from the debrief
- **Accuracy over appearance.**
- **Find the cause before fixing.**
- **No wrong puzzles and no fake progress.**
- **Coaches speak at meaningful moments**, not just because a screen opened.
- **Beginner first.**
- **Less clutter, the same capability.**
- **Every status shows the real state.**
- **A new day brings a new greeting, never a reset.**
- **Recommend where to practise.**

## The user's extra points, 13 Oct
- **43 Welcome music.**
  - It still starts late and has lulls.
  - Bring it in about 3 seconds earlier and remove the long silences.
- **44 First start took 2 to 3 minutes to load.** That's information, not a bug report, but worth a progress line that feels fast and honest.
- **45 The first start felt chaotic.** A Windows shell window, the AI-tier pop-up and a sudden coach appearance spoiled the first impression.
  - Hide the console.
  - Hold the AI card until the player has seen Home.
  - Let the coach arrive calmly after the first screen settles.
- **46 Spelling: British English, not American.**
  - The app mixes "practice" and "practise": 70 against 12 uses.
  - The British rule: the noun is "practice", as in the Practice tab; the verb is "practise", as in "practise it here". Ask the user which they want, then apply British spelling everywhere: colour, analyse and the rest.
- **47 The coaches never say where to practise what.** There's no guided navigation between chess.com and Knightwise. Same as point 38.
- **48 Nothing useful came from Knightwise on chess.com.** The chess.com side feels unworked, with everything concentrated in the app.
  - On chess.com the coaches greeted, then folded. Maya's review appears only on the old address (finding 0). Nothing new or informative appeared there.
  - Product direction: the chess.com side needs real content. Flagship 1, prep before a game, belongs there, along with the review right after a game and warm-ups tied to the habit.
