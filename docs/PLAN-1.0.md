# Knightwise 1.0: the build plan

Agreed with the user on 19 Oct 2026. 1.0 is free forever, with no paywall and no ads, and nothing is taken from
users. It's an indie app, so it must keep working for at least a year with nobody changing its code. It is called
**1.0 only after the user's full hand test passes**; until then it is a beta.

## Flagship 6: Knightwise looks after itself
Agreed on 19 Oct as a flagship and for the trailer, worded only as what's true. Each copy learns from its own player
on their PC; nothing goes to a server.
- **Heals around chess.com changes.** When a button moves or is renamed, the extension looks for it in other ways
  (its words, its shape, its place). Only if it truly can't find it is the feature switched off politely. The fix
  file (A1) is the backup.
- **Learns how you speak.** The text of what the coach heard is kept on the PC (never audio; under 1 MB a year).
  Names, moves and phrases the player uses, and the mishearings that were later resolved, go into that player's own
  hearing hint automatically. The player can look at it, mark mistakes and delete it.
- **Learns how you play.** This already exists: habits, level, openings, spaced repetition.
- **Looks after its own parts.** Engines restart, old files are tidied, and busy AI keys rest and come back.
- **Never claimed:** that it rewrites its own code or learns from all users at once.

## A. Protect the future (first)
1. **The fix file.** Everything the extension finds on chess.com (boards, buttons, tabs), plus an off switch for
   each feature, lives in one small file in the GitHub repo. The app reads it once a day. When chess.com changes, one
   line is edited on github.com and every user is fixed the next day. A switched-off feature says it's resting.
2. **Tests on every change.** They run free on GitHub, and the user gets an email when something breaks. This
   comes on top of the weekly chess.com check that already exists.
3. **The maintainer's handbook** (docs/MAINTAINING.md), written for plain Claude chat. It covers what each file
   does, the exact commands to test and build, and the most likely problems with their fixes.
4. **The extension reloads itself** when the app is newer, so nobody reloads it by hand.

## B. Decided features
5. **Typing does what voice does.** One brain for both: open a review, a rematch, the next step, Prep.
6. **The red ring guides step by step** to the exact chess.com page, tab by tab. It goes on across page changes and
   stops only at the destination. It says "that's not it" on a wrong click, has a Stop button, never rings the
   wrong thing, and never runs during a game. It starts with the places Maya already sends the player.
7. **Feedback by email** to nanotech.mark.robots@gmail.com.
   - It's always in the same place: the sidebar and Maya's box on chess.com.
   - A one-tap 👍 👎 appears at natural endings, at most once a day.
   - No pop-ups, and never during a game.
   - It opens a ready email, or Copy text for people without a mail app.
8. **A weekly report for a human coach**, to print or save as PDF: games, habits, the clock, training done and
   what's next.
9. **Languages.** English by default. One switch in Settings turns everything into Hindi: the app, chess.com, the
   coaches' voices, hearing and AI replies. A native speaker checks the chess words. Other languages only come if a
   volunteer offers.

## C. Novelty and feel
10. **No line twice.**
    - Many versions of every coach sentence, and the app remembers what was said.
    - Jokes stay (casual and chill), but each is used once, then retired.
    - Sentences are built from fresh facts in the player's own games.
    - Training formats rotate, with weekly challenges and personal records. With a key, the AI rewrites the
      same facts in the coach's voice.
11. **Productive, not addictive.**
    - Every session has an end, and every page has one clear next step.
    - Praise goes to effort and habits.
    - Colour has a meaning, and hover effects appear only on what can be clicked.
    - Confetti is rare.
12. **Streaks stay, for practice only.**
    - The fire counter and the week of practice days stay.
    - Habit runs and the losing-streak break stay.
    - Never a streak for just opening the app, and never a pop-up or a "streak lost" scene.

## D. Release
13. **The Edge Add-ons listing**, free, in the same Partner Center (a parent clicks the agreements), with a privacy
    page. Chrome and the other Chromium browsers keep the guided developer install.
14. **The illustrated key guide** in Settings, from the Groq screenshots (with a parent).
15. **The last steps:**
    - Rebuild the installer and put the test copy back as it was.
    - **The user's full hand test**, then fix, retest and fix again until everything is okay.
    - Then 1.0 goes to the Microsoft Store and Edge Add-ons, dev-0.6 merges into main, and Store 0.4.1 is uninstalled.

## Open
- Firefox: later, if wanted. Its extensions work differently (no offscreen page for the voice), so it needs its own work.
