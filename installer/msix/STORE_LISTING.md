# Microsoft Store listing for Knightwise (copy and paste into Partner Center)

## Pricing and availability
- **Markets:** all markets
- **Visibility:** *Public* (1.0 launch, 22 Oct 2026)
- **Pricing:** Free. No free trial needed.

## Properties
- **Category:** Education (subcategory: none). Secondary: Games / Board
- **Privacy policy URL:** https://github.com/Abhra71/ChessCoach/blob/main/PRIVACY.md
- **Website:** https://github.com/Abhra71/ChessCoach
- **Support contact:** nanotech.mark.robots@gmail.com (also Send feedback inside the app)
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

- **A full game review, free.** Every move labelled like the big sites (Book, Best, Mistake, Blunder…), accuracy for
  both players, who's winning move by move, and Maya talking you through it, forwards and back. The key moments explain
  what you played, what was better, and how hard it was for players at your level.
- **Practice made from your own games.** Positions where you went wrong come back until they stick, with puzzles on
  the same idea at your level. Today's 5 minutes, a course from beginner up, and your level, skill by skill.
- **Rematch your loss.** Play a lost game again from the moment it went wrong, against a human-like opponent at about
  their level.
- **Prep before a game.** How someone plays, from their public games: their openings and how their games end. Then
  spar against a player who plays like them.
- **Talk to your coach.** Click Talk and ask Maya anything about your games, out loud. Needs a free key from Groq or
  Google Gemini.
- **Train:** Prep, your opening tree, a repertoire, sparring, In your head, Blindfold, Guess the human move and an
  endgame trainer, all in one place.
- **Your progress:** You vs you, a weekly report for a human coach, your month as Knightwise Wrapped, 20 badges, and
  your best game as a short 3D film.
- **It shows you the way** on chess.com with a red ring around the right link, and never clicks for you.
- **Fair play first.** Knightwise is never active during a game against a real person: no hints, no arrows, nothing.
- **Free and open source.** No account, no adverts, no tracking. It looks after itself when chess.com changes.

Made by Abhra71. Knightwise is an independent app. It is not made by, endorsed by or connected with chess.com.

**What's new in this version**
1.0: A new, calmer look with pictures instead of walls of text. A full game review: every move labelled, accuracy,
an eval bar and a game graph, and Maya speaking each move. Train, a new home for every training tool. Your level as a
ladder you can see. Talking: Maya hands you to Viktor on his pages, and slows down when she teaches. One-click
feedback. Puzzles come with the app, so the first start is quick.

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
