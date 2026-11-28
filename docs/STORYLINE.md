# Knightwise storyline: first draft for the owner (28 Nov 2026)

Status: **draft to read and change.** Nothing here is built yet. Mark anything you don't like; we build only what you
approve. History facts marked † are from memory and get a checked source before they go into the app.

---

## 1. The big idea in one line

**Knightwise is a chess club you joined, not just an app.** Two coaches run it, you're the newest member, and every
page of the app is a room in the club. People come for game review; the club's story makes them stay and learn.

Why a club: a club has people (the coaches), places (the pages), a past (chess history) and your own journey
(ranks). That's everything a storyline needs, and none of it needs the AI: it's written once, by us, and built in.

---

## 2. The coaches: experienced players with a past

First names only, as today (surnames risk matching real players). Clearly fictional, like characters in a novel. They
never claim real titles, results or friendships with real players.

### Maya: the coach who sits beside you
- **Who:** grew up in **Chennai**, India's chess city, where she played in school tournaments from age 7. A strong
  junior: state junior champion at 14. Played open tournaments across Asia in her teens, then chose coaching: "I liked
  watching someone *get it* more than winning myself."
- **How she teaches:** fast, warm, practical. Loves tactics and blitz. Never lets a mistake go by without "here's
  what to look for next time." Understands Hinglish (she grew up with it).
- **Her room:** your games, practice, today's 5 minutes, the chess.com buddy. She's the first face you meet.
- **Little things:** says "one move at a time" when you're on a losing streak; celebrates your first fork with real joy;
  has a running joke about pawns ("the most underestimated piece in the club, like you").

### Viktor: the old master of the club
- **Who:** grew up in **Riga, Latvia**, the city of Mikhail Tal†, the "magician" world champion. Played his
  country's championship for years, never became a grandmaster, and taught at a chess school for thirty years. Has
  studied every World Championship match and keeps a **notebook** of the games that changed chess.
- **How he teaches:** calm, dry humour, patient, a storyteller. Strict about calculation ("see it before you move it").
  Believes every opening has a story and every mistake has a reason.
- **His room:** your progress, your plan, your level, the course, and later the Hall of Champions and the Book's
  history pages.
- **Little things:** opens his notebook when you reach a new rank; remembers your first win; once a month tells a
  short "on this day" story from chess history.
- **His new look:** the owner wants to change it; to discuss separately.

### How they talk together
They're colleagues with different styles. Maya: "Go for it!" Viktor: "Calculate first." Rarely, a two-line exchange
between them on Home (once a week at most), so the club feels alive.

---

## 3. The club: every page is a room

**Menu names stay plain** (Home, Games, Practice...) so nobody gets lost; the club feel lives in the pages' titles,
the coaches' words and small touches.

| Page | Room in the club | What changes |
|---|---|---|
| Home | **The clubhouse** | The greeting, the week's story moment, the coaches' rare banter |
| Games | **Your match records** | Each game a "match" with its story: how it ended, the turning point |
| Practice, Today's 5 minutes | **The training ground** | Maya runs it; sounds and small celebrations |
| Train | **The practice hall** | Prep, blindfold, calculation, endgames: Viktor's drills |
| Your course, later the Book | **The library** | Chapters from "How to read chess" to advanced; Viktor's history pages |
| Your level | **Your membership rank** | The 5 ladder steps become ranks (below) |
| Progress | **Your record** | Your story so far; Viktor's short letter at each milestone |
| Later: master games | **The Hall of Champions** | World Championship games and famous positions, Viktor's notes |
| Later: analysis board | **The analysis room** | The free board with arrows; load any game by name |

---

## 4. Your journey: five ranks

The existing ladder (coach/ladder.py) gets names a club would use. Same skills and targets as today; no rating promise.

| Ladder step (today) | Band | Rank | Viktor's notebook page you unlock |
|---|---|---|---|
| Safe pieces | up to ~800 | **New member** | "Why the greats never hang pieces": how Capablanca kept it simple† |
| Tactics and good starts | ~800–1,200 | **Club player** | "The fork that won a title"; the opening principles |
| Fewer mistakes | ~1,200–1,600 | **Team player** | "Tal's sacrifices: why they worked"† |
| Precision | ~1,600–2,000 | **First board** | "The Berlin Wall": Kramnik's defence that stopped Kasparov in 2000† |
| Expert | 2,000+ | **Club master** | "Deep Blue, 1997, and what came after": Kasparov's Advanced Chess† |

(The Berlin story is exactly the kind of thing the owner heard from Gotham: an opening chosen to stop one man.)

---

## 5. Story moments: small, rare, never in the way

| When | What happens |
|---|---|
| First start | "Welcome to the club." Maya introduces herself in one line; Viktor nods from the side. |
| First game reviewed | Maya: "That's your first match record. Every member's starts somewhere." |
| First practice passed | A small sound and a glow on the board. |
| New rank | A short celebration; Viktor opens his notebook (one page, 3–4 lines, a position you can play through). |
| 7-day streak | Maya notices; a small badge. |
| 100 games checked | Viktor: "A hundred matches. I've seen players quit at ten." |
| One year in the club | A short letter from both: your first game vs now, in numbers. |
| "On this day" (≤ once a month) | One historic game on its anniversary, e.g. 11 May 1997, Deep Blue beats Kasparov†. Skippable. |
| A real World Championship is being played | Viktor mentions it once and offers its games in the Hall of Champions (later). |

Rules: one line per coach bubble; a story comes in crumbs, never a wall; everything skippable; nothing ever appears
during a live game (fair play).

---

## 6. Words: real chess language, explained

The app uses the words strong players use. The first time a word appears, it's underlined: tap it for one plain line
and, where useful, a tiny board. A glossary page lists them all.

| Word | Plain meaning |
|---|---|
| Notation (Nf3, exd5, O-O) | How moves are written: piece letter + square. Nf3 = knight to f3; x = takes; O-O = castles |
| Candidate moves | The 2–3 moves worth thinking about before you choose |
| Hanging piece | A piece that can be taken for free |
| Blunder / mistake / inaccuracy | Big, medium and small slips, measured by the engine |
| Fork | One piece attacks two at once |
| Pin | A piece can't move without exposing a bigger one behind it |
| Skewer | A pin in reverse: the big piece is in front and must move |
| Discovered attack | Moving one piece uncovers an attack by another |
| Double attack | Two threats at once; they can only stop one |
| In-between move (zwischenzug) | A surprise move played before the expected recapture |
| Tempo | One move of time; "gaining a tempo" = making them waste one |
| Development | Getting pieces off the back row into play |
| The centre | The four middle squares; whoever controls them usually has more space |
| Fianchetto | A bishop on the long diagonal after a pawn steps forward (g3 and Bg2) |
| Gambit | A pawn given early for speed or attack |
| Theory / book move | Moves well known from master games |
| Novelty | A move never played before in that position |
| Transposition | Different move orders reaching the same position |
| Open file | A column with no pawns: a highway for rooks |
| Outpost | A safe square in their half where a piece can't be chased by pawns |
| Weak square | A square the opponent's pawns can no longer guard |
| Pawn structure | The shape of the pawns; it decides the plans |
| Isolated pawn | A pawn with no friendly pawns beside it |
| Passed pawn | A pawn no enemy pawn can stop on its way to queen |
| Initiative | Making threats so they're busy answering, not planning |
| Prophylaxis | Stopping their plan before it starts |
| Compensation | Something worth the material you gave up |
| Back-rank mate | Mate on the back row, the king trapped by its own pawns |
| Opposition | Kings facing each other with one square between; who moves loses ground |
| Zugzwang | Any move makes it worse, but you must move |
| Stalemate | No legal move but not in check: a draw |
| Perpetual check | Checks forever: a draw |
| Tablebase | A perfect answer book for endgames with few pieces |

---

## 7. Sound, music and movement (in the same story)

- **Sounds:** soft wood for moves, a gentle chime for a found tactic, a quiet low note for a mistake. Never loud.
- **Music:** calm, low music only in the library and study pages, off by default for games; one switch for all.
- **Movement:** pieces glide; a brief glow on a great move; Maya and Viktor react (nod, smile, think) with light
  animation (Rive). All of it under one second, never blocking a click.

---

## 8. What we will not do

- No fake grandmasters, no invented history, no made-up quotes from real players.
- No text walls; no story in the way of the chess.
- Nothing during a game against a real person.
- No in-app AI writing the story at run time: it's written, checked and shipped.

---

## 9. Questions for the owner

1. **Maya from Chennai, Viktor from Riga:** do these feel right? Other countries in mind?
2. **Rank names** (New member → Club master): keep, or something else?
3. **Club words in the menu**, or plain names (recommended) with the club feel inside the pages?
4. **"On this day" history:** once a month, or more often?
5. **Viktor's new look:** what do you have in mind? (Older, a cardigan and notebook? Something else?)
6. **Music:** in the library only (recommended), or a soft option everywhere?
