# Knightwise: the full test (everything since the 13 Oct debrief)

**Replaced on 20 Oct by [TEST-1.0.md](TEST-1.0.md),** which adds everything built since and marks what Claude proved.

One test on the 0.6 copy, which has all of 0.5.0 (the 48 debrief points) and everything built after it (0.6 to
0.11). About 2 hours, in three sessions; do them on different days if you like. Claude starts the test copy, reads
each step out loud and in the chat, one at a time, and waits for "done" or "next".

For each step, compare with **Expect**. If anything is wrong, slow, ugly or confusing, say the **step number** and
what you saw. Your real data stays untouched.

**Have ready:** Chrome logged in to chess.com, volume up a little. For session C, a parent (the free Groq key).

**Before session B:** Chrome must load the 0.6 extension. Until 19 Oct it loaded the 0.5.0 one
(ChessCoach\extension). In chrome://extensions, remove Knightwise, then Load unpacked and choose ChessCoach-0.6\extension.

**Pre-checked by Claude on 19 Oct:** everything in A except A7.2, the basics of B (B1 to B4), and C3, C4, C10, with
about 25 fixes. That doesn't count as a pass: this test is yours. The hearing was also measured with generated voices
(97.5% of words right, about half a second each); your own voice is measured with the 20-sentence recording page.

**Names:** *Maya* is your coach (the face and the voice). *The human-move model* (Maia) is the chess AI that plays
like real players of a rating. They're different things.

---

# Session A: the app, about 65 minutes

## A1. Home and the first look, 5 minutes
| Step | Do | Expect |
|---|---|---|
| A1.1 | Look at Home | A short "Home" introduction with **Got it**. Maya arrives after the cards settle, not suddenly |
| A1.2 | Press **Got it** | It goes and doesn't come back on Home |
| A1.3 | Press **▶ Hear it from Maya** | Three sentences: your focus, the habit, your last game. A breath between sentences |
| A1.4 | Look at the sidebar | Home, Games, Practice, Your plan, **Your course**, **Your level**, Progress, Settings, and **Send feedback** |

## A2. Practice, 8 minutes
| Step | Do | Expect |
|---|---|---|
| A2.1 | Open **Practice** | The top says "today: N right first time", the bottom "All time: …" |
| A2.2 | Look at a puzzle's rating in its briefing | Near your level (about 300 to 600), not 1,400 |
| A2.3 | Do two positions, go to Home and back | The same positions, your answers kept |
| A2.4 | Ask Claude to restart the app, open Practice | Still the same positions today |

## A3. Game review: one moment at a time, and the why, 12 minutes
| Step | Do | Expect |
|---|---|---|
| A3.1 | Games → open your last lost game | Maya at once: how many key moments, which cost the most, "press Next" |
| A3.2 | Press **Next** through the steps | You played → Better → They replied → Their better, one at a time, each with its own arrows |
| A3.3 | Read the last step | **Why**, from the board: e.g. "Your rook on a8 was already under attack, and g6 did nothing about it" |
| A3.4 | Is the why right? | Say which reasons felt right or wrong. Wrong ones are the most useful |
| A3.5 | Look at **Your clock** | How long you took on the costly move, and your longest think |
| A3.6 | Press **Learn it** | That idea's lesson in Your course opens |
| A3.7 | Back, press **Rematch from here** | The last few moves of the real game play, then your move; they answer at about their level |
| A3.8 | **Take back**, then **Start again** | Both work |
| A3.9 | Games → **Your opening tree** | Every move in words ("You: pawn to e4"); click a row and the board shows it |

## A4. Your course, Your level, Your plan, 15 minutes
| Step | Do | Expect |
|---|---|---|
| A4.1 | **Your course** | Five levels of lessons; "Next for you" at the top with your number and its goal; some "You already do this" |
| A4.2 | Open the next lesson → **Practise it** | The idea, the habit, two moments from your games, then your positions and Lichess puzzles on it |
| A4.3 | **Your level** | Five levels, your numbers from your last 20 games, each skill with a training button |
| A4.4 | Is this you? | Which numbers feel right or wrong |
| A4.5 | **Your plan** | Viktor's cards, no finger pointing at nothing |
| A4.6 | **Progress** | A **Your clock** box: biggest mistakes played in a rush, losses on time |

## A5. The trainers, 20 minutes
| Step | Do | Expect |
|---|---|---|
| A5.1 | Your level → **Endgame trainer** → Mate with king and queen | A fresh position, the idea, a move limit; perfect defence |
| A5.2 | Stalemate it on purpose | "Stalemate" with the tip; Take back works |
| A5.3 | Mate it | Confetti, solved 1× |
| A5.4 | **See it in your head** | The board stays still: put in the whole line as arrows, then Check |
| A5.5 | **Your repertoire** | Three lines: as White, against 1.e4, against 1.d4. Practise one |
| A5.6 | Progress → **Slow-down drill** | Your own rushed positions; tick the checks before the board lets you move |

## A6. Human-like opponents and strong players, 10 minutes
| Step | Do | Expect |
|---|---|---|
| A6.1 | Settings → **Human-like opponents** → On | The switch stays on |
| A6.2 | Games → a lost game → a key moment to the end | A **Real players** line: what 1,100 and 1,500 players play there ("a level ahead of you") |
| A6.3 | Games → **Prep**, type someone you play → **Spar against them: As White** | They answer "their usual move, in N of their games" while their games last |
| A6.4 | Play on past their usual moves | It goes on at about their level |
| A6.5 | Your course → Level 4 → **Your openings' pawn structures** → Practise | Your repertoire's plans, then "find the strong player's move" from 2,400+ games |

## A7. Feedback and closing, 3 minutes
| Step | Do | Expect |
|---|---|---|
| A7.1 | Sidebar → **Send feedback** | Three questions, saved |
| A7.2 | Quit from the icon by the clock | It really closes: nothing called Knightwise left in Task Manager |

---

# Session B: chess.com, about 30 minutes
| Step | Do | Expect |
|---|---|---|
| B1 | Open chess.com home | Maya with her pick, and **Warm up here: 3 positions** |
| B2 | Press **Warm up here** | A small board in her box with your own position; a wrong move: she says why; after 3: "go and play" |
| B3 | Open your games archive | A Knightwise tag under each checked game; Maya explains the tags |
| B4 | Open Puzzles | Maya says she won't look at the board while you solve |
| B5 | Open someone's profile | Maya offers "Prep against them"; on your own profile she doesn't |
| B6 | Play a game against **a real person** | **Nothing at all** from Knightwise while it runs |
| B7 | When it ends, open its review page | Within a minute or two: the review one moment at a time on chess.com's board, Maya's voice, **Your clock**, **Rematch** if you lost |
| B8 | Step to the end of a moment | The why, **Real players**, and **Learn it**, which opens the lesson in Knightwise |
| B9 | Press **Rematch from move N** | Knightwise comes to the front with the rematch |

Bot games: chess.com doesn't share them with apps, so Knightwise can't review them.

---

# Session C: the AI and your voice, with a parent, about 25 minutes
| Step | Do | Expect |
|---|---|---|
| C1 | Settings → **How to get a free key**. With a parent, follow it at console.groq.com | A key starting with gsk_. **Take a screenshot of every Groq page**: they become the picture guide |
| C2 | Paste it into Key 1, **Save key**, **Test key** | A green line; "Talking is on" |
| C3 | On Home, ask Maya "How do I stop leaving pieces hanging?" | A real answer in her words, read aloud |
| C4 | In a game review, **Explain like a coach** | A longer explanation; no squares or moves that aren't on the board |
| C5 | Press **🎙 Talk** and say "Hi Maya, how am I doing?" | She hears you in about half a second, answers out loud, listens again |
| C6 | Say "Review my game against" and an opponent's name | That review opens |
| C7 | Say "next" a few times, then "rematch it" | Each step said out loud; the rematch opens |
| C8 | Say nothing for 8 seconds | She stops listening: "I'll be here" |
| C9 | On chess.com, press **🎙 Talk** in Maya's box | The first time, a Knightwise page asks to allow the microphone; then she answers |
| C10 | On chess.com, type to Maya | Her own words; off-topic gets a friendly steer back to chess |

## Also note down
- Anything that took longer than 3 seconds.
- Any text you had to read twice.
- Your "is this me?" on the why, the course, your level and the clock.

Then: the fixes, a last check on the installed app, and the update on the Store (with a parent).
