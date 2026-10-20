# The Knightwise trailer

**Made by Knightwise itself (20 Oct, second cut after the owner's notes):** `Videos\Knightwise\Knightwise trailer.mp4`,
88 seconds, 1920×1080, H.264 + AAC (what the Microsoft Store and YouTube take); `Knightwise trailer (phone).mp4` is the
same at 720p, under 30 MB. Cut like an action-film trailer: slow and tense, then fast, then slow again.

- **Two songs, one switch** (Kevin MacLeod, CC BY 4.0): "Hitman" (tense) until its last hit at 26.55 s, a silence with
  one line, then "Ready Aim Fire" from the bar before its crash, so the title lands on the crash; the rock stops dead
  on a bar at 77.5 s and rings out. The first cut was off the beat: its rock was placed by loudness (2.3 s), but the
  real crash is at 3.41 s. Now **every cut is on a measured beat**: `installer/trailer/beats.mjs` (onsets, loudness and
  cymbal crashes, in a hidden Edge) and `track.py` (beat tracking); the beats are written into `trailer.html`.
- **Voices** (`installer/make_trailer_voice.py`, Kokoro): a narrator (Viktor's voice, slowed: "Every game you lose… has
  a lesson in it. Most players never find it. Now… you will."), and each coach on screen, once, saying who they are.
- **Every part of the app, by name**, full screen and sharp (the film look is only on the title cards): review, practice,
  five minutes a day, rematch, guess the human move, prep, ask your coach, the plan, the level ladder, the course,
  progress, Wrapped, the chess.com check, the film; then fair play, free, no account, no ads.
- **Credits inside the film**, each at its moment: Kokoro when Maya first speaks, Stockfish on the mistakes found,
  Maia-3 on "How hard was it?", Lichess on practice, python-chess on the rematch, the Lichess Elite Database on the
  guess, the chess.com public API on prep, Whisper and Groq on asking out loud, the Lichess opening catalogue on the
  course, Three.js and Poly Haven on the film, Kevin MacLeod on the title. "Abhra Chakraborty presents… Knightwise" at
  the start; Knightwise, then "Developed by Abhra Chakraborty", at the end.
- **Opponents' names never appear** ("Opponent").

**To make it again** (after the app changes):
1. `python -m coach.get_assets --trailer` (the two songs and mp4-muxer, once), and `python installer/make_trailer_voice.py`.
2. Record the clips: the app running on port 8766, then, from `installer/trailer`,
   `node rec.mjs scenes.json ../../coach/ui/vendor/trailer` (it drives a hidden Edge over its DevTools port: real pages,
   scripted clicks, opponents' names hidden). The cut itself is in `coach/ui/trailer.html`.
3. Open `http://127.0.0.1:8766/ui/trailer.html`: **▶ Play** to watch, **Make the video (MP4)** to save it (`?phone` for the small copy). It's made
   frame by frame, never live, so a slow or hidden window can't drop frames.

---

## The first plan: the script and shot list for recording by hand

About 80 seconds. One shot per flagship, real screens with your real games, nothing staged that the app doesn't do.
Every claim is true and checkable: no rating promises.

**Tools, all free and already on Windows 11:**
- Record each shot with the **Snipping Tool's** video mode, or **Game Bar** (Win + Alt + R starts and stops).
- Put it together in **Clipchamp**: the clips in order, the text on top, the music, Maya's voice-over.
- Maya's lines are ready as sound files: `Videos\Knightwise\trailer\` (made by `installer/make_trailer_voice.py`,
  with Maya's own voice).
- Music: the film's track, once you've picked it. Loud in the gaps, lower under Maya's voice.

**Before recording:** the 0.6 extension loaded, voice on, Settings → Theme → Dark, window full screen, chess.com
logged in. Close other tabs and notifications (Focus on).

| # | Seconds | On screen (how to get it) | Text on screen | Maya says (file) |
|---|---|---|---|---|
| 1 | 0–6 | The welcome film: start Knightwise with `try fresh` and record the first seconds | **Knightwise** | – (music only) |
| 2 | 6–14 | chess.com: one of your finished games, Maya's review stepping through a moment, with arrows on chess.com's own board | Your mistakes, on chess.com's own board | "I go through your games with you, one moment at a time." (01) |
| 3 | 14–21 | The end of that moment: the why and **How hard was it?** | Why it went wrong. And how hard it was. | "Only two in ten players at your level find this. So let's learn it." (02) |
| 4 | 21–28 | Practice: a position from your own game, the briefing, you find the move | Practice made from your own games | "Your practice comes from your own games." (03) |
| 5 | 28–36 | Games → a lost game → **Rematch from here**, a move or two | Replay the moment it went wrong | "Play it again from where it went wrong, against someone at their level." (04) |
| 6 | 36–43 | chess.com profile → **Prep against them** → their openings → **Spar** | Before you play them: their openings, their double | "Before you play someone, I show you how they play." (05) |
| 7 | 43–50 | **🎙 Talk**: "Maya, what should I work on?", Stop, her answer | Talk to your coach. Out loud. | (her real answer) |
| 8 | 50–56 | chess.com: "take me to the bots", the red ring from Learn to Play to Play Bots | It shows you the way. It never clicks for you. | "Click Play Bots, in the red ring." (06) |
| 9 | 56–66 | Progress → your best game → the film, the winning move and its caption | Your best game, as a film | – (music up) |
| 10 | 66–71 | Settings → chess.com check: **All working** | It looks after itself | "When chess.com changes, I find my way again." (07) |
| 11 | 71–80 | A black end card, white text | **Free. No account. No ads.** · Never active in a game against a real person. · **Knightwise** on the Microsoft Store | "Knightwise. Free, and fair." (08) |

**Never in the trailer:** a game against a real person with Knightwise showing anything; a rating number as a
promise; other players' names you haven't asked to show (blur opponents' usernames, or use games against bots and
friends who said yes).

**Also for the Store:** the same screens as stills make the Store screenshots (1920×1080). Shots 2, 3, 5, 8 and 9
are the strongest.
