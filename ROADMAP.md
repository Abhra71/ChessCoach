# Knightwise: where we are and what comes next

*Hand-over notes for the next work session (updated 11 Oct 2026). Read this after CLAUDE.md.*

## Where we are
- **Microsoft Store:** Knightwise **0.4.1** (MSIX, `Abhra71.Knightwise`, Store ID `9NKLGS6K72J2`) submitted for
  certification on 11 Oct 2026 as a **private beta** (group "Knightwise beta", free). Install link once it passes:
  https://apps.microsoft.com/detail/restricted/9NKLGS6K72J2. Store page text: `installer/msix/STORE_LISTING.md`.
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

## Build order
1. **Welcome screen redesign** (the builder's latest request, details below).
2. **Remove "Play the Coach"** (never wanted).
3. **Extension guide with the builder's real screenshots** (`screenshots-raw/9-11.png`, gitignored): crop, remove other
   extensions and the OneDrive name (profile picture may stay), type the extension path into the folder dialog's
   address bar, mark the clicks in red; note that Developer mode must stay on and Chrome's "unsafe" warning is expected.
4. **The coach character on chess.com** (extension overlay, voice, appears when chess.com opens, greets with the focus).
5. **Instant review on chess.com** after a game ends.
6. **Navigation guide** (highlight, then check).
7. **Suggestions and progress**; **AI key walkthrough**; **voice commands through the AI**.
8. Optional: **Builder mode** in Settings (replay welcome, start fresh as a new player in a separate profile).
Each change ships as a Store update (new MSIX, version bump); update `STORE_LISTING.md` when what players see changes.

## Welcome screen redesign (requested 11 Oct 2026)
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
