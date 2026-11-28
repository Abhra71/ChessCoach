# Knightwise's tools: the studio's departments

Started 28 Nov 2026. The owner directs; each department is a trusted tool that does one job. **Rule:** a tool is
installed when its phase starts (not all at once), and only if it is reliable, widely used, well maintained and
really helps Knightwise; its licence must fit GPL-3.0. Each entry says why it was chosen. Claude checks the current
version and licence on the day it is installed and updates this file.

## Checking tools (they look at the app and report)

| Department | Tool | Status | Where it runs | Why this one |
|---|---|---|---|---|
| Logic tests | pytest + GitHub Actions | ✅ since Oct | PC + GitHub, every push | The standard for Python; 317 tests |
| UI | **Playwright** 1.65.2 (Microsoft, Apache-2.0) | ✅ 28 Nov | PC: `check-ui.bat` | Drives the PC's own Edge like a player; screenshots of all 17 pages at 2 sizes |
| Code quality | **Ruff** 0.17.6 (MIT) | ✅ 28 Nov | PC + GitHub, every push | The fastest, most used Python checker; set to real-bug kinds only (`ruff.toml`). First run found `/api/stats` always failing |
| Security | **CodeQL** (GitHub, free for public repos) | ✅ 28 Nov | GitHub: every push to main + Mondays | GitHub's own scanner, Python + JavaScript; results in Security → Code scanning |
| Fair play | Fair-play audit + its tests | ✅ | PC + GitHub | `docs/FAIR-PLAY-AUDIT.md` |
| Accessibility | **axe-core** (Deque, MPL-2.0) | ⏳ with the storyline UI work | inside the UI check | The industry standard; contrast, labels, readable text |
| UI overlaps | Extra rule in the UI check | ⏳ next UI upgrade | PC | Catches a coach bubble covering buttons (seen at 1000×680 on Home, 28 Nov) |
| Library alerts | **Dependabot alerts** (GitHub) | ⏳ owner clicks: Settings → Code security → Dependabot alerts | GitHub | Warns when a library we pin has a known hole; no automatic upgrade PRs (versions change on purpose only) |
| Store package | **Windows App Certification Kit** (Microsoft, in the Windows SDK) | ⏳ before the next Store submission | PC | Microsoft's own pre-check of the MSIX; not in the light build tools (`build/sdktools`), needs the SDK installer with only the kit ticked |
| Code review | **Claude on GitHub** (claude-code-action) | ⏳ needs a token the owner creates | GitHub, on pull requests | A second reader for every change; check it works on the owner's plan first |
| Weekly memo | A scheduled run of all the above, one short summary | ⏳ after the departments above exist | PC or GitHub | For the owner, the head of the studio |

## Making tools (they become part of the app; each installed at its phase)

| Phase | Tool | For | Size | Why this one |
|---|---|---|---|---|
| Analysis board | **chessground** (Lichess, GPL-3.0) | The board: arrows, circles, smooth moves | ~1 MB | Used by Lichess for millions daily; the same licence family as ours |
| Analysis board | **chess.js** (BSD-2) | Moves and notation in the page | <1 MB | The standard JavaScript chess rules library |
| Storyline, life | **Rive** runtime (MIT) | Coaches that move and react | ~1–2 MB | Light, smooth, made for interactive characters |
| Storyline, life | **lottie-web** (MIT) | Celebrations, short effects | ~0.3 MB | The common format for app animations |
| Feel (step 4) | **PixiJS** (MIT) | Particles and effects on the graphics card: embers and glow for Viktor's burnt notebook, celebrations, a brilliant move | ~0.5 MB | The standard fast 2D effects engine for the web |
| Life | **Kenney** sounds (CC0), **Freesound** (CC0 only) | Move and UI sounds | ~5 MB | No strings attached |
| Life | **Incompetech / Kevin MacLeod** (CC BY, credited) | Calm study music | ~20 MB | Widely used, clear licence |
| Book | Public-domain classics (Project Gutenberg): Capablanca *Chess Fundamentals* (1921), Lasker *Common Sense in Chess* (1896) | Teaching backbone, in our own words | ~1 MB | World champions' own teaching, free |
| Book, history | **Wikipedia** (CC BY-SA, credited, each fact linked) | Dates, places, who played whom | – | Checkable sources |
| Hall of Champions | World Championship game moves (facts) from a source with clear terms | Master games | ~2–5 MB | Checked licence first |
| Book, endgames | **Lichess tablebase** (online, optional) | Exact endgame answers | 0 | Perfect play; the app works without it |

Already inside: three.js (MIT, the 3D Game-of-the-month film), Stockfish 19 (GPL-3), Maia-3, python-chess (GPL-3), Kokoro voice (Apache-2.0), Lichess puzzles and
openings (CC0), pywebview, onnxruntime. Every credit goes on an "About and thanks" page in the app.
