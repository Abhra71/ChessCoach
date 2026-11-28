# Knightwise: the learning station plan (everything decided, 28 Nov 2026)

One page to keep: the owner's ideas from 28 Nov, every decision, the tools, the files, and the order of work.
Details live in the linked files.

---

## 1. Where it started
The owner wanted to learn the English Opening, went to Gotham Chess on YouTube, and only then remembered Knightwise
has a repertoire. Coming back, it **drilled the line as a puzzle before teaching it**, with little explanation.
That pain became the plan: Knightwise should teach, not only test.

## 2. The vision
- **Knightwise becomes a complete chess learning station** (it's listed under Education): from the basics (not how
  pieces move; notation upwards) to 2,000+, for casual and serious players.
- **Players come to *view*, not to *use*.** The app's duty is to make them feel; the coaches' duty is to make them
  crave to use it. People come for game review; the story pulls them into learning.
- **Professional, not a toy:** real chess vocabulary (explained), history and nostalgia, a storyline across the
  whole app, a professional feel (animation, environment, sound), lively but never chaotic.
- **The PC version is the flagship.** The phone version is a companion built for the phone, not a copy (like
  Warzone vs Warzone Mobile), and points players to the PC version.

## 3. Decisions and rules
| Rule | Detail |
|---|---|
| Code, not the in-app AI | The AI is the weak spot; it stays only for chat. Chapters and stories are written at build time, Stockfish-checked, sourced, shipped as files |
| Use trusted tools, credit them | Don't build everything from scratch; Knightwise's value is the direction and how the pieces connect |
| Nothing unused | Every feature needs a right-time moment from the player's data, its data used, and a reason in the story (CLAUDE.md; tests/test_connected.py) |
| Fair play | Off in every live game. **The analysis board has no engine at all** (it's the creators' explaining board). Engine help only in review and practice of finished games |
| No backend | GitHub Pages, the phone's own engine, the player's own Drive (owner, 28 Nov) |
| One thing at a time | Say what, explain, test, then build; a short summary after |
| Releases in steps | 1.3, 1.4…: each a Store update and a promotion moment |
| Exams first | Work for the owner resumes after exams (1–11 Dec) |

## 4. What gets built (PC, in order)
| # | Step | What | Files |
|---|---|---|---|
| 1 | Feature map | Every feature with its moments, story reason, data; coverage test | docs/CONNECTIONS.md |
| 2 | Use record + picker | Features come back when the need returns (today: once opened, never again) | docs/CONNECTIONS.md |
| 3 | Storyline in the app | The Knightwise Club, ranks, ~175 chess words in 3 layers (tap to explain), Viktor's regret, Maya's moments, moments for Blindfold, Guess the move, Game of the month, Wrapped | docs/STORYLINE.md |
| 4 | Feel | Polished cartoon coaches (Rive), Viktor's new look, environment reactions, sound, music, one calm motion system; then every new feature ships with its motion | docs/TOOLS.md |
| 5 | Analysis board | Move both sides, arrows, circles, set up, load any famous game or position by name ("Carlsen vs Gukesh", "Lucena"); no engine; the phone builds it first, the PC reuses it | |
| 6 | The Book (the hero) | **Grows from Your plan** (owner, 28 Nov): the plan's Explore search is already a dictionary of chess (every tactic, ending and opening); the Book makes each entry a chapter. Chapter 0 "How to read chess", chapter 1 the English Opening; then batches of ~10; each chapter: explain → show → try → drill, linked to the player's own games; ~150 chapters over 6–8 months. Your course stays a separate lesson path | |
| 7 | Hall of Champions | World Championship games and famous positions with the coaches' notes; search by players / tournament / year | |
| 8 | Lichess | The player's Lichess games too | |
| 9 | Centaur mode | Kasparov's Advanced Chess: you + the engine's top 3 candidates vs the engine; a small side feature | |
| – | Mobile | Its own chat, in parallel, limited scope (below) | docs/MOBILE-PLAN.md (mobile branch) |

**Hero feature:** the Book + the player's own games: "learn it, then see it in your own game". The Book alone isn't
enough (libraries exist everywhere); the link to your games is what nobody else has.

**Rough timeline after exams:** steps 1–6 (first chapters) → release **1.3 "The Learning Station"** about 3 months
in; Lichess + Centaur → **1.4**; the Book keeps growing alongside. App size: about 420–450 MB (376 MB today).

**Chapter checking without the owner reading 150 chapters:** Stockfish checks every move and claim automatically,
every history fact needs a source, the owner tastes about 1 in 10 plus the beginner ones as a learner, players get a
"was this clear?" button, and a strong player reviews the advanced chapters later.

## 5. The storyline (docs/STORYLINE.md, draft 2)
- **The Knightwise Club:** every page a room (clubhouse, training ground, library, Hall of Champions, analysis room);
  menu names stay plain.
- **Maya:** from Chennai, a former state junior champion who chose coaching; warm, fast, tactics, understands
  Hinglish. Relatable moments: her hung queen at her first tournament, the junior final lost on time (→ the clock
  drill), seven losses in a row (→ "one more game only if the last one was fun"), memorising vs understanding
  (→ the Book).
- **Viktor:** from Berlin, Germany (Lasker's city), played the German championship, taught for 30 years, keeps a notebook of the
  games that changed chess. **His regret:** one win from the title, he played the quick move without checking the
  winning combination and lost ("I lost to a move I didn't check") → why he teaches calculation. A second regret:
  he never wrote his games down → why he values your match records.
- **Five ranks** on the existing ladder: New member → Club player → Team player → First board → Club master, each
  opening a page of Viktor's notebook (e.g. the Berlin Defence that stopped Kasparov in 2000).
- **Every mode has a reason** in the coaches' lives (table in the file).
- **Tone:** one or two lines, ends in something useful, never cringe, regrets told once, nothing during live games.
- **Open questions for the owner:** the countries, rank names, menu names, how often "on this day", Viktor's new
  look, music where.

## 6. The studio: departments and tools
**Chats = departments** (shared board: `C:\Syntax_Assembler\knightwise-studio\STATUS.md`, private):
- **PC app (the main ChessCoach-0.6 chat):** everything in the Windows app and extension, tools and installs,
  tests, Store submissions and updates.
- **Mobile:** the phone version. Scope: your finished games and key moments, today's 5 minutes and streak, your
  numbers and focus, the analysis board (chessground, no engine), Stockfish Lite (1.9 MB) on finished games only,
  a home-screen shortcut and swiping through moments, a pointer to the PC version.
- **Promotions:** posts, reels, Instagram @abhra71_dev, X, HN, creators, campaign links, analytics.
- The owner is the **head of the studio**; each new chat gets its own department.

**Checking tools (docs/TOOLS.md):**
| Tool | Status |
|---|---|
| pytest + GitHub tests | ✅ 318 tests |
| Playwright UI check (`check-ui.bat`, uses the PC's Edge) | ✅ 17 pages × 2 sizes, screenshots in logbook/ui-check |
| Ruff (real bugs only) | ✅ on PC and GitHub; first run found the practice page never resumed today's answers: fixed |
| CodeQL security | ✅ weekly on GitHub |
| test_connected (nothing unused) | ✅ |
| Overlap rule, accessibility (axe-core) | next UI upgrades (Maya's bubble covers Home in small windows) |
| Dependabot alerts | owner clicks: GitHub Settings → Code security |
| Windows App Certification Kit | before the next Store submission |
| Claude code review on GitHub | later, needs a token the owner creates |
| Weekly memo for the owner | after the departments above |

**Making tools, each installed at its phase:** chessground + chess.js (board), Rive (coaches), Lottie
(celebrations), web animations (board, pages), Kenney and Freesound CC0 sounds, Incompetech music (credited),
public-domain classics (Capablanca, Lasker), Wikipedia (credited), World Championship game moves, the Lichess
tablebase (optional). Already inside: Stockfish 19, Maia-3, python-chess, Kokoro voice, Lichess puzzles and
openings.

**Storage on the owner's PC:** about 3.3 GB for development today, about 3.6–4 GB with all tools; 262 GB free.

## 7. Where things stand today (28 Nov)
- **Live:** Knightwise 1.1 on the Microsoft Store. **1.2** built (quiet updates, ask box can rematch, fair-play
  audit, bug hunts), not yet submitted.
- **Done today:** the checking departments, the /api/stats fix, the nothing-unused rule and test, the storyline
  draft, the connection design, the departments and the status board.
- **Owner:** started CS50P (Python); exams 1–11 Dec.
- **Next:** step 1, the feature map (needs nothing from the owner).
