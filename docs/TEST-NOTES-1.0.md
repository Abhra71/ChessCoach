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
