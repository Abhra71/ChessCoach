# Microsoft Store listing for Knightwise (copy and paste into Partner Center)

## Pricing and availability
- **Markets:** all markets
- **Visibility (first release):** *Private audience*: only the testers listed; switch to *Public* when testing is done
- **Pricing:** Free. No free trial needed.

## Properties
- **Category:** Education (subcategory: none). Secondary: Games / Board
- **Privacy policy URL:** https://github.com/Abhra71/ChessCoach/blob/main/PRIVACY.md
- **Website:** https://github.com/Abhra71/ChessCoach
- **Support contact:** https://github.com/Abhra71/ChessCoach/issues
- **Product declarations:** tick "This app depends on non-Microsoft drivers or NT services": **no**.
  "Accessibility guidelines": leave unticked.
- **System requirements:** Minimum: 8 GB memory, x64. Recommended: 16 GB.

## Age ratings (questionnaire)
Category: *Reference, educational or informational app*. Answer **no** to everything (no violence, no user-to-user chat,
no purchases, no location sharing). It does use the internet. Expected rating: 3+ / Everyone.

## Store listing (English)
**Description**

Knightwise is a chess coach that sits beside you on chess.com. It reads your finished games, finds the habits that
really cost you points, and trains you out of them, one thing at a time, at your level.

- **Your real mistakes, explained.** Stockfish checks every move you played. Knightwise shows the moments that mattered,
  like the piece you left hanging or the fork you walked into, and what to play instead. Try it again turns any of them into a puzzle.
- **Four coaches, nothing to set up.** Maya reviews your games, Arjun runs puzzles and practice, Zara gets you ready
  to play and Viktor tracks your progress. They have faces, gestures and their own voices, on chess.com and in the app.
- **Arrows on chess.com.** With the free Knightwise browser extension, your finished games get the better move and
  the reply drawn on chess.com's own board.
- **Today's 5 minutes.** One position from your own games, one puzzle and your opening, every day. A gentle streak, no guilt.
- **Practice with a briefing.** Before every position the coach tells you which game it comes from, what's going on
  and the mindset to bring. 30,000 Lichess puzzles in 20 themes, matched to your rating.
- **Progress you can see.** You vs you, the story of your week, your opening tree and 20 badges earned in real games.
- **Fair play first.** Knightwise never helps during a game against a real person. No hints, no arrows, nothing.
- **Free and open source.** No account, no adverts, no tracking. Optional AI replies use your own free key from Groq
  or Google Gemini.

Made by Abhra71. Knightwise is an independent app. It is not made by, endorsed by or connected with chess.com.

**What's new in this version**
0.5.0: Meet your four coaches, Maya, Arjun, Zara and Viktor. They appear on chess.com and in the app, talk with their
own voices, react to your moves and stay away during games against real people. New: Today's 5 minutes, a briefing
before every practice position, Your plan with an opening that suits you, Try it again, your opening tree, You vs you,
the story of your week, 20 badges, sounds, and a new welcome with quiet piano. Add a free AI key to talk with your coaches.

**Product features** (one per line)
- Finds your real mistake patterns in your chess.com games
- Four coaches with faces and voices, on chess.com and in the app
- Better-move arrows on chess.com's board with the free extension
- Today's 5 minutes, practice with a briefing, puzzles at your level
- Progress, your opening tree and badges from your real games
- Strict fair play: never active in games against real people
- Free, open source, no account, no tracking

**Short description:** A chess coach that sits beside you on chess.com: your real mistakes, two coaches with voices, practice at your level.

**Keywords:** chess, chess coach, chess.com, stockfish, chess puzzles, chess training, game review

**Additional information / "Notes for certification"** (Submission options → Notes for certification):

> Knightwise is a desktop chess coach (Python app packaged as MSIX, runFullTrust). To test without a chess.com account,
> type the public username "gushynanda" on the welcome screen; the app downloads that user's public games and
> analyses them with the bundled Stockfish engine (first check takes a few minutes). The AI explanations are optional
> and need a user-supplied key, so they can be skipped. The browser extension is optional and loaded by the user from
> Documents\Knightwise\extension. runFullTrust is needed because the app runs the bundled Stockfish chess engine
> as a separate process and a local web server on 127.0.0.1 for its own window. The microphone is used only when the
> player presses Talk, and speech is transcribed on the device. The app starts with Windows (a startup task the user can turn off)
> and waits by the clock to check for new games.

## Screenshots (1366×768 or larger, PNG)
Ready in `installer/store-shots/`, 1920×1080 PNG: on chess.com, Home, review, practice with a briefing, Today's 5 minutes, Progress, opening tree, welcome.

## Store logos
`installer/StoreLogo2160.png` (2160×2160: the 1:1 box art) and `installer/StorePoster1440x2160.png` (9:16 poster art).
