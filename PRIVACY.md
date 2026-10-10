# Knightwise privacy policy

*Last updated: 10 October 2026*

Knightwise is a free, open-source chess coach for Windows (source code: https://github.com/Abhra71/ChessCoach).
It is made by one person (Abhra71). There are no accounts, no adverts and no tracking.

## What stays on your PC
Everything Knightwise learns about your chess stays on your own computer:
- your chess.com username, your downloaded games, the mistakes it finds and your practice progress
  (in your Windows user folder: `AppData\Local\ChessCoach`);
- your voice: speech is turned into text **on your PC** by a built-in speech model. No audio is ever sent anywhere;
- the coach's spoken voice is also made on your PC.

If you add an AI key (optional), it is stored in **Windows Credential Manager**, encrypted by Windows,
and is only ever sent to the AI company it belongs to.

## What is sent over the internet, and to whom
| When | Sent to | What |
|---|---|---|
| Checking for new games | chess.com (public API) | your chess.com username, to download your public games |
| First start | lichess.org (public puzzle database) | nothing about you; it downloads free puzzles |
| You turn on listening | huggingface.co | nothing about you; it downloads the speech model |
| You use "Explain like a coach" or ask a question, **only if you added an AI key** | the AI company whose key you added (Google Gemini, Groq, Anthropic or OpenAI) | the chess position, the engine's facts about the moment, your rating and your typed or spoken question |

Each of those companies handles that request under its own privacy policy. Knightwise does not send anything to its
maker, and it collects no analytics, crash reports or usage statistics.

## The browser extension
The optional Knightwise browser extension only talks to the Knightwise app on your own PC (`127.0.0.1`). On
chess.com it reads which finished game is open so it can draw the coach's arrows. It sends nothing to anyone else.

## Fair play
Knightwise never gives help during a game against a real person: no hints, no arrows, no reading the board.

## Children
Knightwise does not knowingly collect personal information from anyone, including children.

## Deleting your data
Uninstall Knightwise, then delete the folder `%LOCALAPPDATA%\ChessCoach`. To remove an AI key, use Settings → Remove,
or delete the "ChessCoach" entries in Windows Credential Manager.

## Contact
Questions: open an issue at https://github.com/Abhra71/ChessCoach/issues
