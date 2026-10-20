# Knightwise 1.0: your hand test, and what Claude already proved

This replaces TEST-FULL.md (19 Oct). Everything since then is in it. Do it on the 0.6 test copy: your real data
is untouched. About 2.5 hours, in three sessions; different days are fine. Claude starts the test copy, reads each
step out, one at a time, and waits for "done" or "next".

For each step, compare with **Expect**. Anything wrong, slow, ugly or confusing: say the **step number** and what
you saw. "Not believing my results" is the right attitude: this test is the real one.

## How to read the marks
- ✅ **Claude checked it**, and the **Proof** column says how. Still yours to judge: Claude checks that it does what
  Claude meant, only you can say it does what you meant.
- ⚠️ **New in the last two days.** Most of the bugs will be here. Look hardest at these.
- ❓ **Claude couldn't check it** (your microphone, your ears, a real game against a person, your taste). Test first.

## What the machine checks on every change (no need to test by hand)
- **187 automated tests** pass on this PC and on GitHub's own computer, which emails the owner when one fails.
- Every library is fixed to the exact version tested; a rebuild can't pick up a newer one by surprise.

**Have ready:** Chrome logged in to chess.com, volume up a little. For session C, a parent (the free Groq key).

**Before session B:** Chrome must load the 0.6 extension. Until now it loaded the 0.5.0 one (ChessCoach\extension).
In chrome://extensions: remove Knightwise, then **Load unpacked** and choose `ChessCoach-0.6\extension`.
Claude can't do this one: it's a folder dialog.

---

# Session A: the app, about 75 minutes

## A1. Home, 5 minutes
| Step | Do | Expect | Mark · Proof |
|---|---|---|---|
| A1.1 | Look at Home | One clear next step: **Start** on Today's 5 minutes is the only bright button | ✅ counted on all 18 pages (design pass) |
| A1.2 | Press **▶ Hear it from Maya** | Three sentences: your focus, the habit, your last game | ✅ 19 Oct |
| A1.3 | Close the app and open it twice more | Maya greets you differently each time; no sentence twice in a row | ⚠️ new · ✅ tested: every version is used before one comes back |
| A1.4 | Look at the sidebar | It says **Voice on** or **off**, matching Settings | ⚠️ fixed today (it said "on" when off) |

## A2. Practice and today, 8 minutes
| Step | Do | Expect | Mark · Proof |
|---|---|---|---|
| A2.1 | Open **Practice**, do two positions | One bright button at a time ("I'm ready", then the board) | ✅ |
| A2.2 | Go to Home and back | The same positions, your answers kept | ✅ 19 Oct |

## A3. A game review, 12 minutes
| Step | Do | Expect | Mark · Proof |
|---|---|---|---|
| A3.1 | Games → your last lost game | Maya: how many key moments, which cost the most | ✅ |
| A3.2 | Press **Next** to the end of a moment | You played → Better → They replied → Their better; then the **why** | ✅ |
| A3.3 | Read **How hard was it?** | "Only 2 in 10 players at your level find this. Missing it is normal at your level." Does it feel kind and true? | ⚠️ new (human-move model) · ✅ seen on test moments |
| A3.4 | Read **Real players** | What players at your level play there, and players 400 points above you | ⚠️ new wording · ✅ |
| A3.5 | **Rematch from here** | They answer like a human of their level (the human-move model, now at any rating) | ⚠️ new model · ✅ tested legal at ratings 100 to 2,000 |
| A3.6 | A game you **won** → **▶ Watch it as a film** | See A8 | ⚠️ |

## A4. Course, level, plan, 10 minutes
| Step | Do | Expect | Mark · Proof |
|---|---|---|---|
| A4.1 | **Your course**, open the next lesson | Its idea, two moments from your games, then practice | ✅ 19 Oct |
| A4.2 | **Your level** | Five levels; your numbers from your last 20 games | ✅ 19 Oct |
| A4.3 | Is this you? | Which numbers feel right or wrong | ❓ yours |

## A5. The new trainers, 25 minutes
| Step | Do | Expect | Mark · Proof |
|---|---|---|---|
| A5.1 | Your level → **Weekly challenge: guess the human move** | "Black to move. What would a 1,000 player play?" on a real position | ⚠️ new · ✅ played all 5 in the app: 323/500 |
| A5.2 | Guess the most played move | **100 points**, the three most played moves with bars, and what the engine prefers | ✅ (a rounding bug that gave 99 was fixed) |
| A5.3 | Finish the five, then **Try again** | Your best this week is kept; the same five until Monday | ✅ tested |
| A5.4 | Your level → **Blindfold** → **Listen** | Maya reads the start of one of **your own games**; the board stays empty | ⚠️ new · ✅ with the voice off (moves shown one at a time); ❓ how it sounds |
| A5.5 | Answer on the empty board | Right: "You saw it without the board", the next one a move longer. Wrong: where it really was, on the real position | ✅ tested both |
| A5.6 | With a key (session C): **Say the square** | Say "f three": it answers for you | ❓ needs your microphone |
| A5.7 | **Endgame trainer**, **See it in your head**, **Repertoire** | As before; no confetti for each calculation line any more | ✅ |

## A6. Progress, the report and Wrapped, 10 minutes
| Step | Do | Expect | Mark · Proof |
|---|---|---|---|
| A6.1 | Progress → **Report for your coach** | Your week in facts: summary, games, mistakes a game against the week before, habits, practice, best game, the costliest move and the better one, what's next | ⚠️ new · ✅ seen with test data |
| A6.2 | **Month** | The same for 30 days | ✅ |
| A6.3 | **Print or save as PDF** | The print window; the PDF looks clean on white | ❓ Claude couldn't open the print window |
| A6.4 | **▶ Play it as Wrapped** | Big cards one at a time, Viktor saying each; click or the arrow keys; confetti at the end | ⚠️ new · ✅ cards seen; ❓ the voice |

## A7. Settings, 5 minutes
| Step | Do | Expect | Mark · Proof |
|---|---|---|---|
| A7.1 | **Human-like opponents** | On by default now; it says it plays like real players of any rating, "never a real person" | ⚠️ changed |
| A7.2 | **What the coach heard** list | The text of what you said by voice (never audio); Delete clears it | ❓ not yet checked in a browser |
| A7.3 | Sidebar → **Send feedback** → **Send by email** | Your mail app opens a ready email to nanotech.mark.robots@gmail.com; or **Copy text** | ❓ not yet checked |

## A8. Your game as a film, 5 minutes
| Step | Do | Expect | Mark · Proof |
|---|---|---|---|
| A8.1 | Progress → your best game ("Watch it as a film"), **▶ Play** | The antique set from your side, high up; quiet moves quickly | ⚠️ new · ✅ seen in Chrome |
| A8.2 | The winning moves | It slows down, the camera leans in, a caption: "Move 21. Your queen takes their queen on e5: check!" | ✅ seen |
| A8.3 | The end | "Checkmate. You won." card | ✅ seen |
| A8.4 | Is the board the right way round? | Your pieces at the bottom, the a-file on your left | ✅ fixed today: the 3D set itself is a mirror image |
| A8.5 | **Save as a video** | It plays once, then the file opens in Videos\Knightwise. Does it play in Windows? | ❓ not yet tried |
| A8.6 | Is it worth watching? | Your honest verdict. If it isn't, it goes | ❓ yours |
| A8.7 | The music | Comes once you've picked a track | waiting for your pick |

---

# Session B: chess.com, about 35 minutes (the 0.6 extension loaded first)
| Step | Do | Expect | Mark · Proof |
|---|---|---|---|
| B1 | chess.com home | Maya with her pick, and **Warm up here: 3 positions** | ✅ 19 Oct |
| B2 | Press **Warm up with puzzles** (or ask "take me to the puzzles") | A **red ring** around chess.com's own **Solve Puzzles**; Maya: "Click Solve Puzzles where the red ring is" | ⚠️ new · ✅ tested on the real pages (with Claude's copy of the code, not the loaded extension) |
| B3 | From **Learn**, ask for the bots | Ring on **Play**; click it; on the Play page the ring moves to **Play Bots**: "Good. Now click Play Bots" | ⚠️ ✅ same |
| B4 | On the way, click something else | "That's not it, no problem. Click … in the red ring." After three wrong turns she stops | ⚠️ ✅ same |
| B5 | **Stop showing me** | The ring goes | ⚠️ |
| B6 | Your games archive | Knightwise tags under your games | ✅ 19 Oct |
| B7 | Type to Maya: "open my last review" | It opens: typing does what voice does | ✅ 19 Oct |
| B8 | Someone's profile | "Prep against them" | ✅ 19 Oct |
| B9 | **Play a game against a real person** | **Nothing at all** from Knightwise while it runs: no ring, no Maya | ❓ the hard line: Claude never plays games for you |
| B10 | Its review page afterwards | The review one moment at a time on chess.com's board, with **How hard was it?** | ⚠️ |

---

# Session C: the AI and your voice, with a parent, about 25 minutes
| Step | Do | Expect | Mark · Proof |
|---|---|---|---|
| C1 | Settings → **How to get a free key**, at console.groq.com with a parent | A key; **take a screenshot of every Groq page** for the picture guide | ❓ needs you and a parent |
| C2 | Paste it, **Save key**, **Test key** | A green line; "Talking is on" | ✅ 19 Oct (your keys work) |
| C3 | Press **🎙 Talk** in the app | "I'm listening. Click Stop when you've finished." It **keeps listening** until you click | ⚠️ changed today, as you asked · ✅ tested with a stand-in microphone |
| C4 | Say "How am I doing?", click **■ Stop** | She answers in about **2 seconds**, out loud; Talk is back for your next turn | ⚠️ · ✅ 1.6 s after Stop (it took up to 33 s before today's fix) |
| C5 | Talk: "Review my game against" an opponent | That review opens | ✅ 19 Oct |
| C6 | Talk: "next", then "rematch it" | The next step; the rematch | ✅ 19 Oct |
| C7 | On chess.com, **🎙 Talk** in Maya's box, then Stop | The same: click, speak, Stop | ⚠️ changed today · ❓ not tried with a real microphone |
| C8 | On chess.com, Talk: "take me to the bots" | The red ring starts | ⚠️ new · ✅ the action is tested |

## Also note down
- Anything that took longer than 3 seconds.
- Any text you had to read twice.
- Your "is this me?" on the why, How hard was it, your level and the report.

Then: Claude fixes everything you found, you retest those steps, and 1.0 goes to the Store and Edge (with a parent).
