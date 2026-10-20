# The Knightwise trailer

**Made by Knightwise itself (20 Oct):** `Videos\Knightwise\Knightwise trailer.mp4`, 76 seconds, 1920×1080, H.264 + AAC
(what the Microsoft Store and YouTube take). Cut like an Indian action-film trailer, the owner's brief: slow and tense,
then fast, then slow again, so there's time to take in each move.

- **Songs, each where it fits** (Kevin MacLeod, CC BY 4.0): "Hitman" for the slow, tense opening (0–27 s) and the last
  hit (66 s); "Ready Aim Fire" for the rock, from the title drop (27.2 s, its riff at 2.3 s); "Jalandhar" for the slow
  motion into the checkmate, then silence on the king. Every cut is on a beat (172 a minute in the rock).
- **Credits inside the film**, each at the moment its part pays off: Stockfish when the better move's arrow lands, Maia-3
  on "How hard was it?", Lichess on practice, and so on. "Abhra Chakraborty presents" at the start, "Developed by Abhra
  Chakraborty" at the end.
- **Opponents' names never appear** ("Opponent").

**To make it again** (after the app changes):
1. `python -m coach.get_assets --trailer` (the two songs and mp4-muxer, once).
2. Record the clips: the app running on port 8766, then, from `installer/trailer`,
   `node rec.mjs scenes.json ../../coach/ui/vendor/trailer` (it drives a hidden Edge over its DevTools port: real pages,
   scripted clicks, opponents' names hidden). The cut itself is in `coach/ui/trailer.html`.
3. Open `http://127.0.0.1:8766/ui/trailer.html`: **▶ Play** to watch, **Make the video (MP4)** to save it. It's made
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
