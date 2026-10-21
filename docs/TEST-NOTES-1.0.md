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

Also asked: Home after the newest 20 games, the rest checked in the background (offered, not yet decided).
