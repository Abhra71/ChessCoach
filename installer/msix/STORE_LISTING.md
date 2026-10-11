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

Knightwise is a chess coach that sits behind you. It reads your finished chess.com games, finds the habits that
really cost you points, and trains you out of them, one or two things at a time, tuned to your rating.

- **Your real mistakes, explained.** Stockfish checks every move you played. Knightwise shows the moments that mattered:
  the piece you left hanging, the fork you walked into, the checkmate you missed. Each comes with what to do instead.
- **Arrows on chess.com.** With the free Knightwise browser extension, open any finished game on chess.com and see
  the better move and the opponent's reply drawn on the board itself.
- **A coach that talks.** Knightwise speaks its advice in a natural voice, and you can ask it questions out loud.
  Speech is processed on your PC.
- **Practice that sticks.** Puzzles from your own games and from the Lichess puzzle database, repeated on a
  schedule until you've learned them.
- **Fair play first.** Knightwise never helps during a game against a real person. No hints, no arrows,
  nothing. It coaches you before and after.
- **Free and open source.** No account, no adverts, no tracking. Optional AI explanations use your own free key
  (Google Gemini or Groq).

Made by Abhra71. Knightwise is an independent app. It is not made by, endorsed by or connected with chess.com.

**What's new in this version**
0.4.2: a new welcome: a short 3D chess film with quiet piano (mute any time), opening full screen. A clearer,
step-by-step guide with real pictures for adding the chess.com arrows extension. A fresh start
after every reinstall. Removed the in-app practice game so the coach stays focused on your chess.com games.

**Product features** (one per line)
- Finds your real mistake patterns in your chess.com games
- Better-move arrows on chess.com's board (free browser extension)
- Spoken coaching, and questions by voice, processed on your PC
- Spaced-repetition practice from your own games and Lichess puzzles
- Strict fair play: never active in games against real people
- Free, open source, no account, no tracking

**Short description:** A chess coach for chess.com players: your real mistakes, explained by voice, with arrows on the board.

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
To be taken from the app: Home, Game review with a key moment, Practice, Settings, the welcome screen, the arrows on chess.com.

## Store logos
`installer/StoreLogo2160.png` (2160×2160: the 1:1 box art) and `installer/StorePoster1440x2160.png` (9:16 poster art).
