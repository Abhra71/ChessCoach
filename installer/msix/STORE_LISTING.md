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

Knightwise is a free chess coach that sits beside you on chess.com. It reads your finished games, finds the habits
that really cost you, and trains you out of them, one thing at a time, at your level.

- **Your real mistakes, explained.** Stockfish checks every move you played. Maya, your coach, goes through the moments
  that mattered on chess.com's own board: what you played, what was better, and why. "How hard was it?" tells you how
  many players at your level would have found the better move.
- **Practice made from your own games.** Positions where you went wrong come back until they stick, with puzzles on
  the same idea at your level. Today's 5 minutes, a course from beginner up, and your level, skill by skill.
- **Rematch your loss.** Play a lost game again from the moment it went wrong, against a human-like opponent at about
  their level.
- **Prep before a game.** How someone plays, from their public games: their openings and how their games end. Then
  spar against a player who plays like them.
- **Talk to your coach.** Click Talk and ask Maya anything about your games, out loud. Needs a free key from Groq or
  Google Gemini.
- **New ways to train:** Guess the human move, the weekly challenge; Blindfold, following your own games in your head;
  an endgame trainer and calculation practice.
- **Your progress:** You vs you, a weekly report for a human coach, your month as Knightwise Wrapped, 20 badges, and
  your best game as a short 3D film.
- **It shows you the way** on chess.com with a red ring around the right link, and never clicks for you.
- **Fair play first.** Knightwise is never active during a game against a real person: no hints, no arrows, nothing.
- **Free and open source.** No account, no adverts, no tracking. It looks after itself when chess.com changes.

Made by Abhra71. Knightwise is an independent app. It is not made by, endorsed by or connected with chess.com.

**What's new in this version**
1.0: The human-move model now plays like real players of any rating, beginners included. How hard was it? on every
review moment. Guess the human move, the weekly challenge. Blindfold by voice. Your best game as a 3D film. A weekly
report for your coach and your month as Wrapped. Talk: click to talk, click Stop to send, answers in about two
seconds. The red ring guides you step by step on chess.com. Coaches never say the same line twice in a row.

**Product features** (one per line)
- Finds the habits that cost you, from your real chess.com games
- Your coach reviews your games on chess.com's own board
- Practice and puzzles made from your own mistakes, at your level
- Rematch your loss against a human-like opponent
- Prep and sparring before a game against a real player
- Talk to your coach by voice (with a free AI key)
- Strict fair play: never active in games against real people
- Free, open source, no account, no tracking

**Short description:** A free chess coach that sits beside you on chess.com: your real mistakes, explained, and practice made from them.

**Keywords:** chess, chess coach, chess.com, stockfish, chess puzzles, chess training, game review

**Additional information / "Notes for certification"** (Submission options → Notes for certification):

> Knightwise is a desktop chess coach (Python app packaged as MSIX, runFullTrust). To test without a chess.com account,
> type the public username "gushynanda" on the welcome screen; the app downloads that user's public games and
> analyses them with the bundled Stockfish engine (the first check takes a few minutes). AI replies and Talk are
> optional and need a key the user supplies (Groq or Google Gemini), so they can be skipped. The browser extension is
> optional and loaded by the user from Documents\Knightwise\extension. runFullTrust is needed because the app runs
> the bundled Stockfish chess engine as a separate process and a local web server on 127.0.0.1 for its own window.
> The microphone is used only while the player has clicked Talk and until they click Stop; the recording is sent
> only to the AI provider the player chose, with their own key, to be written down as text, and the text is kept on
> the device. The app starts with Windows (a startup task the user can turn off) and waits by the clock to check for
> new games.

## Screenshots (1366×768 or larger, PNG)
Ready in `installer/store-shots/`, 1920×1080 PNG: on chess.com, Home, review, practice with a briefing, Today's 5 minutes, Progress, opening tree, welcome.

## Store logos
`installer/StoreLogo2160.png` (2160×2160: the 1:1 box art) and `installer/StorePoster1440x2160.png` (9:16 poster art).
