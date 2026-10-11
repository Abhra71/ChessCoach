# Knightwise: where we are and what comes next

*Hand-over notes for the next work session (updated 11 Oct 2026). Read this after CLAUDE.md.*

## Where we are
- **Microsoft Store:** Knightwise **0.4.1** (MSIX, `Abhra71.Knightwise`, Store ID `9NKLGS6K72J2`) submitted for
  certification on 11 Oct 2026 as a **private beta** (group "Knightwise beta", free). Install link once it passes:
  https://apps.microsoft.com/detail/restricted/9NKLGS6K72J2. Store page text: `installer/msix/STORE_LISTING.md`.
  **Passed certification on 11 Oct 2026 (about 30 minutes) and is live as a private beta ("In Microsoft Store").**
  Updates: Partner Center → Knightwise → Start update (upload a new MSIX with a higher version).
- **After it passes:** install from the link, uninstall the old "Chess Coach" (Settings → Apps), remove the old Chrome
  extension and load `Documents\Knightwise\extension`. Old backups in `%LOCALAPPDATA%\Programs\ChessCoach`
  (`_internal-0.3.0-backup`, `ChessCoach-0.3.0-backup.exe`) can then be deleted.
- **Local testing (builder):** the old installed Chess Coach 0.4.0 has the same screens. Open
  `http://127.0.0.1:8765/#/welcome` (or `#/home`) in a browser while it runs. The `chesscoach://` link on this PC is
  missing its open-command (offered to fix; not done).
- Smart App Control blocks any unsigned build on the builder's PC, so only Store-signed builds can be run there.

## The vision (confirmed by the builder, 11 Oct 2026)
A grandmaster-level coach that **appears when chess.com opens**:
1. An **animated character** on the chess.com page, a text box under it showing what it says, and a voice.
   Its expressions change (pleased / worried / thinking).
2. It **greets you and suggests what to do** (warm-up puzzles, which bot or mode to play).
3. **Silent in any game against a real person** (fair play). Reviews it **right after**, move by move, with arrows
   on chess.com's board.
4. **Guides you around chess.com** ("click Puzzles"), checks whether you did it, highlights the spot if not.
5. **Builds your history**: where you improve and where you don't.
6. **Suggests curated puzzles**, plus extra curated training in the app (premium quality, free).

Today the "brain" exists (Stockfish review of every game, habits, practice, voice, AI explanations, in the app window).
The "body" on chess.com (character, voice there, navigation, instant review) does not.

## Decisions
- **Stockfish decides all chess.** The AI never judges a position.
- **Our code:** reading the chess.com page (no screen capture), navigation highlights, the fair-play gate (the AI never
  receives positions from a live game against a person), progress, the character's expressions (driven by the engine).
- **AI:** the coach's words, understanding what the player says (speech → intent → action, no sentence patterns),
  personality and memory. **Highly personalised per player**: a short player card (rating, habits, progress, preferred
  tone, things they said) goes with the engine facts; one or two points at a time.
- Works without a key (ready-made sentences from engine facts); better with the player's own free key (Gemini, Groq).
- **No auto-clicking on chess.com** (terms-of-service risk): the coach points, the player clicks, the coach checks.
- **Help during bot games:** not until chess.com confirms it's allowed (their rules ban help "during play").
  Draft a message to chess.com support for the builder.
- **Adding an AI key:** a guided in-app walkthrough with **real screenshots** (Google AI Studio first, Groq second),
  red circles on the click spots, a paste box that tests the key and turns green. The builder takes the screenshots;
  personal details are cropped or blurred.

## 0.4.2 (built 11 Oct 2026, waiting for the builder to upload)
`dist/Knightwise-0.4.2.0.msix` (327 MB). Store screenshots (1920x1080, welcome first) in `dist/store-screenshots`.
Done: Store app keeps its data in its package LocalState (fresh start per install; the builder chose a fresh start
for themself too); window opens maximised; cinematic welcome (film with depth of field, typed lines, Satie
Gymnopedie No. 1 by Michael Laucke, public domain, ~18% volume, fades in, mute remembered); Play the Coach removed;
extension guide uses real Chrome screenshots (`installer/make_guide_shots.py`); README has screenshots.
Notes: `?shot=N` starts the film on shot N (for screenshots/trailer). AI keys live in Windows Credential Manager,
so they survive a reinstall. The old Chess Coach uses the same port (8765): while it runs, Knightwise defers to it,
so it must be uninstalled.

## The big update (decided 11 Oct 2026): 0.4.2 is held and ships together with the coaches on chess.com
No beta testers yet, so one big Store update instead of 0.4.2 now. **Waiting for the builder's go-ahead before building.**

**Four original coaches, nothing to pick, no switch option.** Two women, two men, original faces and names (never real
players' likeness: personality rights, Store rules, false endorsement). Each always appears for the same sections, so it
feels like a specialist; the brain (Stockfish + our facts) is identical. Full expressions for all (pleased, worried,
thinking, talking, blinking), driven by engine facts. Draft (names/ages/voices to confirm):
- Maya (woman, calm former champion): game reviews, instant review after a game.
- Arjun (man, young prodigy): puzzles and practice.
- Zara (woman, bold attacker): before you play: greeting, suggestions, navigation guide on chess.com.
- Viktor (man, veteran): progress and history, lessons, endgames. New sections go to whoever fits best.
Voices: Kokoro voices already installed (samples in dist/voice-samples); builder picks one per coach.
Art style: flat cartoon or illustrated portrait (builder picks). Drawn by us, nothing downloaded.

**How they talk (written sentences + optional AI, merged):**
- Always: written sentences in each coach's own style, many wordings per situation picked at random, plus memory
  ("last week 3 hanging pieces, this week 1"). Free, instant, offline, never wrong.
- With the player's free key (Gemini, Groq): real two-way conversation, questions answered in the coach's personality.
  The AI only words the engine's facts; our code checks every move/square it mentions against them, else falls back.
- Never fails: if both AI providers are busy or down, the coach answers with a written sentence in a positive tone and
  the conversation goes on; a small note says replies are briefly simpler.
- Not hidden: everyone is told clearly, in the app and by the coach, "Add a free key (2 minutes, guided) and you can
  talk with your coaches and get replies." Optional, never nagging.
- No AI running on the PC (builder's decision). Live games are never sent to any AI (fair play).

### Big update progress (11 Oct 2026, evening; builder away, provisional choices)
Built and committed (tested with mock chess.com pages in build/preview, not yet in the builder's Chrome):
- coach/coaches.py: four coaches, sections, written sentences per coach, moods; /api/coach.
- extension/faces.js (flat cartoon, 4 moods, blink, talking mouth), buddy.js/css (allow-list of sections; hidden on
  play/game/battle pages), voice via offscreen.html; Maya heads the review panel.
- Instant review (archive-gated), navigation guide (red ring on chess.com's Puzzles link, never clicks).
- Chat: /api/chat, coaches.chat (persona, square check, never-fail fallback); ask box only with a key; the app's
  ask boxes explain the free-key feature instead of a disabled field. Not tested with a real key (none on this PC).
Provisional (builder to confirm): voices Maya bf_emma, Arjun am_puck, Zara af_nova, Viktor bm_george; flat style.
Also done: Viktor's weekly memory. Left: AI key walkthrough with the builder's screenshots, voice
questions on chess.com, Settings note about the coaches, README/Store text, test in the builder's Chrome with
`try.bat`, screenshots, build 0.5.0.

### Built on the night of 11 Oct 2026 (builder away, tested on real chess.com + the app in the builder's Chrome)
- 12 gestures for the four coaches; neck fixed; character centred on the box.
- Library from real data: 30,000 Lichess puzzles in 20 themes (data/puzzles.json, v2), the Lichess opening catalogue
  (coach/openings, CC0). The Lichess opening explorer now needs a Lichess login, so it isn't used.
- coach/plan.py: the sense (stalemated wins, new mistakes, opening trouble, losing streak, stuck habit, fresh idea);
  Your plan tab; Zara brings the new thing on chess.com ("Learn it in Knightwise" opens the app there).
- App: coaches on every tab, reactions on every board move, AI card at the right moments, green chess.com board.
Next: AI key guide (needs the builder's screenshots), real-key test of chat, voice questions on chess.com,
an AI-written "new idea" when a key exists, build 0.5.0, Store text and screenshots.

### Next big piece (the builder, 12 Oct 2026; waiting for the hearing choice)
- Voice-to-voice conversation with the coach of each field, not a text chat: hold to talk, she answers out loud, and the turns continue.
- "Review my game against X" by voice: the coach finds the game, opens it, and talks through every move: what you played,
  what was better, and one new thing to learn. Finished, archived games only.
- A two-way bridge: app to chess.com, which opens the game on chess.com with Maya there; chess.com to app, which opens the right page.
  Every pop-up has navigation to where it makes sense.
- Hearing: recommended, the player's free Groq or Gemini key, so nothing AI runs on the PC; or Chrome's speech recognition, chess.com only;
  or local Whisper. The builder will choose.

### Hooked by value (builder's go-ahead, night of 11-12 Oct 2026; all in 0.5.0)
- Sounds: the builder picked each one on a picker page from Kenney's CC0 packs (coach/ui/sounds, 81 KB): move, capture,
  check, right, wrong, finished (with confetti), coach arriving, button click. Own switch in Settings; no background music.
- Motion: pieces slide, numbers roll up, lines draw themselves, bars and rings fill.
- No brackets in anything the player reads; shorter lines everywhere.
- Home redesigned (the builder found the "Where your games go wrong" box cramped): Today's 5 minutes on top; focus with a
  sparkline and Practise this; habits as clickable tiles (each opens practice for that habit, fewer or more lately);
  You vs you; rating with a win bar; last game in one line from Maya. The big trend chart and the totals row are gone.
- Today's 5 minutes (coach/daily.py): own position, puzzle on today's idea, first 3 moves of your opening; streak
  forgives one missed day.
- Progress tab with Viktor (coach/progress.py): story of the week (or the last 10 games), saved as a picture to
  Pictures\Knightwise; badges from real games only (Safe pieces, Fork-proof, Safe king, Clean games, Daily habit).
- Try it again: any key moment as a puzzle with Maya. Your opening tree (coach/tree.py) with a note on costly branches;
  found for the builder: as Black against 1.d4, 23%, 10 of 35 losses.
- README rewritten as honest marketing: real numbers only (30,000 puzzles, 3,865 openings, 0.7 vs 1.2 pieces a game,
  45% vs 25% wins), what it doesn't do.
Next: the animated preview for the README needs ffmpeg (ask first); the builder's verdict on the new Home and sounds.

### Vision widened (builder, 11 Oct 2026 night): "a grandmaster sitting beside you" (proposal, awaiting confirmation)
- Gestures and faces per situation, per coach: greet (wave), explain (open palm), point (towards the ring), celebrate,
  encourage (fist pump), think (chin), worried (cheek), warn (raised finger), listen (tilt), goodbye; smooth moves.
- On chess.com, before/after games: what to do and what NOT to do today, from the player's data (e.g. which time
  control, rated puzzles slowly instead of Rush, take a break after 3 losses).
- In the Knightwise app: the same coaches pop up by themselves on each tab and on key buttons, with voice; the board
  looks like chess.com's (colours/feel; our own pieces); a "Your plan" section: ONE opening that suits the player's
  games, one strategy idea, one endgame, taught on the board; curated practice with memory of past mistakes.
- Boards: full live guidance on Knightwise's own boards; on chess.com puzzles/lessons only habits and encouragement
  (never solving rated puzzles); bot games only if chess.com allows; games against people: never.

## Found after the Store launch (11 Oct 2026, builder's first use of 0.4.1)
- **No welcome screen on first start:** the Store app reads `%LOCALAPPDATA%\ChessCoach` (`paths.HOME`), the same
  folder the old Chess Coach uses, found `player.txt` and went straight to Home. Fix in 0.4.2: the Store app keeps its
  data in its own package storage, so uninstalling wipes it and a reinstall shows the welcome again (no accounts;
  Google sign-in to keep progress across reinstalls is a later idea).
- **Window opened small and low, not centred:** `create_window(width=1240, height=820)` with no position. Fix: open
  maximised.
- **Music:** FreePD.com has closed. Options offered (Wikimedia Commons, free to use): Satie Gymnopédie No. 1
  (Michael Laucke, public domain) chosen and shipped in 0.4.2.
- **Making public:** stays a private beta until the welcome redesign, the coach on chess.com (steps 4–5) and the AI-key
  walkthrough are in and a few beta testers have used it. Remind the builder then.
- **GitHub:** make the repo page industry-grade (README with real screenshots/GIF walkthroughs, accurate features,
  install steps, releases) as part of each update.

## Build order
1. ~~Welcome screen redesign~~ (done in 0.4.2).
2. ~~Remove "Play the Coach"~~ (done in 0.4.2).
3. ~~Extension guide with the builder's real screenshots~~ (done in 0.4.2) (`screenshots-raw/9-11.png`, gitignored): crop, remove other
   extensions and the OneDrive name (profile picture may stay), type the extension path into the folder dialog's
   address bar, mark the clicks in red; note that Developer mode must stay on and Chrome's "unsafe" warning is expected.
4. **The coach character on chess.com** (extension overlay, voice, appears when chess.com opens, greets with the focus).
5. **Instant review on chess.com** after a game ends.
6. **Navigation guide** (highlight, then check).
7. **Suggestions and progress**; **AI key walkthrough**; **voice commands through the AI**.
8. Optional: **Builder mode** in Settings (replay welcome, start fresh as a new player in a separate profile).
9. **Store trailer video** (builder asked, 11 Oct 2026): about 45–60 s, 1920×1080 MP4, made by recording the app
   itself (3D welcome film, a game review with arrows, practice, the coach on chess.com once built), titles typed on
   screen, the coach's Kokoro voice as narrator and quiet piano underneath. Needs ffmpeg (ask before downloading)
   and a 16:9 "Super hero art" image (the 3D board, no title text) for the trailer to show at the top of the Store page.
   Also: put the 3D welcome screenshot first in the Store listing.
Each change ships as a Store update (new MSIX, version bump); update `STORE_LISTING.md` when what players see changes.

## Welcome screen redesign (requested 11 Oct 2026)
- Started (not yet committed or tested when this was written): `coach/ui/backdrop.js` camera "film" (high above → glide
  down beside the pieces → follow each move → slow orbit) and higher piece hops. Test it in the browser before shipping.
- **Layout:** the welcome card sits on the **right 30–40%** of the screen as a solid, crisp black panel
  (no blurred glass), with a short professional line and the set-up steps. The **left 60–70%** is the 3D scene.
- **Typed lines** over the scene: short phrases typed letter by letter, held, then erased, for example
  "Every move you played, checked." / "Your habits, found." / "A coach that never sleeps."
- **Cinematic camera** (keep the Poly Haven chess set, which the builder likes): start high, looking straight down;
  glide down close to the pieces at their height with depth of field (background softly out of focus); pieces
  **lift, arc and land** with a shadow and the camera follows; a slow orbit; dark vignette edges like a spotlight.
- **Soft piano music**, very quiet (about 15–20%), fades in over 3 seconds, only on the welcome screen, with a mute
  button that's remembered. Preferred source: a real CC0 recording (e.g. FreePD.com). **Ask before downloading**
  (name, size, licence); offer 2–3 to choose from. Fallback: piano generated in code.

## Recent fixes (for context)
- 0.4.1: the first start always shows the welcome screen (the start-up task hides the window only once set up); the
  welcome says "never sells or shares your data" instead of "sends your data anywhere".
- AI: if a provider retires the model in use (404/410), the app picks the current one from the provider's list and
  retries (Gemini prefers `gemini-flash-latest`).
