# 0.5.0 test session: findings

The session ran on 12 Oct 2026 from a fresh start, using `try.bat fresh`, with Claude guiding by voice.
These are Claude's notes. The user keeps their own list and will debrief at the end.
Fix everything here, from major to minor, before publishing 0.5.0.

## Where to resume
- **Not done yet:**
  - Part 7.5–7.8, a full game against a **real player**:
    - No coach may appear during the game.
    - After it ends, Maya brings the review on chess.com.
    - Then the game shows up in Games in the app.
  - Part 8.3: run `try.bat` without "fresh" and check that the real data is back, unchanged.
  - Part 9, the AI with a Groq key, which is optional.
  - Then the user's own debrief.
- **Watching chess.com:** Claude can't attach to the user's own Chrome tab. It watches with full-screen screenshots, using a script in the scratchpad that calls SetProcessDPIAware. Look only at whether a coach shows during a game, never at the position.

## Major
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
