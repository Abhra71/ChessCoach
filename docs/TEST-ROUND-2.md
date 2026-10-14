# Knightwise 0.5.0: Round 2

About 45 minutes. Claude says each step out loud and in the chat, one at a time, and waits for "done" or "next".
For each step, compare with **Expect**. If anything is wrong, slow, ugly or confusing, say the **step number**
and what you saw. Round 1 was 13 Oct (docs/TEST-SESSION.md); this round checks the fixes for your 48 points and
the new things.

Before you start:
- Claude starts the test copy (your real data stays untouched). If the old Knightwise 0.4.1 from the Store is
  running, the new copy closes it by itself (14 Oct: the old one started with Windows and answered instead).
- Open Chrome and log in to chess.com. Volume up a little.

---

## 1. Home and the first look, 5 minutes

| Step | Do | Expect |
|---|---|---|
| 1.1 | Look at Home | A short "Home" introduction at the top with **Got it**. Maya arrives after the cards settle, not suddenly |
| 1.2 | Press **Got it** | It goes and doesn't come back on Home |
| 1.3 | Press **▶ Hear it from Maya** | Three sentences: your focus, the habit, your last game. A breath between sentences |

## 2. Practice and Today's 5 minutes, 8 minutes

| Step | Do | Expect |
|---|---|---|
| 2.1 | Open **Practice** | An introduction. The top says "today: N right first time", the bottom says "All time: …". They no longer look like two different answers |
| 2.2 | Look at a puzzle's rating in its briefing | Near your level (about 300 to 600), not 1,400 |
| 2.3 | Do two positions, then go to Home and back | The same positions, your answers kept |
| 2.4 | Close the app, ask Claude to start it again, open Practice | Still the same positions today: a restart doesn't change today's set |

## 3. Game review, one moment at a time, 8 minutes

| Step | Do | Expect |
|---|---|---|
| 3.1 | Games, open your last game | Maya at once: how many key moments, which cost the most, "press Next" |
| 3.2 | Press **Next** through the steps | You played → Better → They replied → Their better, one at a time, each with its own arrows and Maya saying it |
| 3.3 | Look at **Your clock** | How long you took on the move that cost the most, and your longest think, from chess.com's clock |
| 3.4 | Press **Rematch from here** (on a game you lost) | The last few moves of the real game play, then it's your move. Play something better and play on: they answer at about their level |
| 3.5 | Press **Take back**, then **Start again** | Both work |
| 3.6 | Games → **Your opening tree** | "How your games start": a how-to-read box, every move in words ("You: pawn to e4"). Click a row: the board shows it |

## 4. Progress and Your plan, 4 minutes

| Step | Do | Expect |
|---|---|---|
| 4.1 | Open **Progress** | A **Your clock** box: how many of your biggest mistakes were played in a rush, and losses on time |
| 4.2 | Open **Your plan** | Viktor's cards, with no finger pointing at the wrong thing |

## 5. chess.com, 15 minutes

| Step | Do | Expect |
|---|---|---|
| 5.1 | Open chess.com home | Maya with her pick, and **Warm up here: 3 positions** |
| 5.2 | Press **Warm up here** | A small board in her box with your own position. A wrong move: she says why. A right one: next. After 3: "go and play" |
| 5.3 | Open your games archive | A Knightwise tag under each checked game. Maya explains the tags and picks your latest game |
| 5.4 | Open Puzzles | Maya says she won't look at the board while you solve |
| 5.5 | Play a game against **a real person** | **Nothing at all** from Knightwise while it runs |
| 5.6 | When it ends, open its review page | Within a minute or two: Maya's review one moment at a time, the board moving to each step, her voice starting after about 3 seconds, **Your clock**, and **Rematch** if you lost |
| 5.7 | Press **Rematch from move N** | Knightwise comes to the front with the rematch |

Bot games: chess.com doesn't share them with apps, so Knightwise can't review them. That's chess.com's limit, not a bug.

## 6. The AI, with a parent, 8 minutes

| Step | Do | Expect |
|---|---|---|
| 6.1 | Settings → **How to get a free key**. With a parent, follow it at console.groq.com | A key that starts with gsk_. Take a screenshot of each Groq page: they go into the guide (point 32) |
| 6.2 | Paste it into Key 1, **Save key**, **Test key** | A green line. "Listening" and the AI card now say the real state |
| 6.3 | On Home, ask the coach "How do I stop leaving pieces hanging?" | A real answer in Maya's words, read aloud |
| 6.4 | In a game review, press **Explain like a coach** | A longer explanation; no squares or moves that aren't on the board |
| 6.5 | On chess.com, type to Maya | She answers in her own words; something off-topic gets a friendly steer back to chess |

## Also note down
- Anything that took longer than 3 seconds.
- Any text you had to read twice.
- Your "is this me?" on the review, the clock and the rematch.

Then Round 3: the same checks on the installed app, the way a new player gets it.
