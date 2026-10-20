# Knightwise privacy policy

*Last updated: 20 October 2026 (Knightwise 1.0)*

Knightwise is a free, open-source chess coach for Windows (source code: https://github.com/Abhra71/ChessCoach).
It is made by one person (Abhra71). There are no accounts, no adverts and no tracking.

## What stays on your PC
Everything Knightwise learns about your chess stays on your own computer, in the app's own folder
(the Microsoft Store app keeps it in its private folder, and uninstalling removes it):
- your chess.com username, your downloaded games, the mistakes it finds and your practice progress;
- the **text** of what you said to the coaches by voice, so the hearing learns the names you use. Never the sound.
  You can read it and delete it in Settings → What your coaches heard;
- the coaches' spoken voices, which are made on your PC;
- films of your games, if you save one (in your Videos\Knightwise folder).

If you add an AI key (optional), it is stored in **Windows Credential Manager**, encrypted by Windows, and is only
ever sent to the AI company it belongs to.

## What is sent over the internet, and to whom
| When | Sent to | What |
|---|---|---|
| Checking for new games | chess.com (public API) | your chess.com username, to download your public games |
| You use Prep or Spar on a player | chess.com (public API) | that player's username, to download their public games |
| Once a day | GitHub (raw.githubusercontent.com) | nothing about you: it reads Knightwise's fix file, the names of things on chess.com's pages |
| Downloads, the first time | lichess.org, Hugging Face, Poly Haven and similar | nothing about you: free puzzles, the voices and 3D files |
| The endgame trainer | Lichess's endgame tablebase | the position on the board; nothing about you |
| You type to a coach, or ask for an explanation, **only with an AI key** | the AI company whose key you added (Groq, Google Gemini, Anthropic or OpenAI) | your question, the chess position or moment, the engine's facts and your rating |
| You click **Talk**, **only with an AI key** | the AI company whose key you added (Groq or Google Gemini) | the recording of what you said, from the moment you click Talk until you click Stop, to be written down as text. Then your question as above |
| You press **Send by email** in Send feedback | your own email app | the feedback you wrote, ready for you to send or not |
| You press **Share** on your week | the app you pick (WhatsApp, X or Instagram) | a line about your week and its picture, for you to post or not |

Each of those companies handles its request under its own privacy policy. Knightwise does not send anything to its
maker on its own, and it collects no analytics, crash reports or usage statistics. Feedback only reaches the maker
if you send the email yourself.

The microphone is on only after you click Talk, and until you click Stop (at most a minute).

## The browser extension
The optional Knightwise browser extension only talks to the Knightwise app on your own PC (`127.0.0.1`). On the
chess.com pages where it may appear, it reads which finished game is open (to draw the coach's arrows) and the
links and buttons it points at with its red ring. It sends nothing to anyone else.

## Fair play
Knightwise never gives help during a game against a real person: no hints, no arrows, no reading the board.

## Children
Knightwise does not knowingly collect personal information from anyone, including children.

## Deleting your data
Uninstall Knightwise: the Store app's data is removed with it. (The older installer kept it in
`%LOCALAPPDATA%\ChessCoach`: delete that folder.) To remove an AI key, use Settings → Remove, or delete the
"Knightwise" entries (and any older "ChessCoach" ones) in Windows Credential Manager. Saved films are in
Videos\Knightwise.

## Contact
Questions: open an issue at https://github.com/Abhra71/ChessCoach/issues
