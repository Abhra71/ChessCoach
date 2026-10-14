# Knightwise flagships

The rule, from 12 Oct 2026: every flagship is something chess.com does not have, and it's free.
A friend who plays on chess.com asked why anyone would use our practice and coach instead of chess.com's own.
"We have puzzles and reviews too" is not an answer. These are.

Before adding anything new, ask: does chess.com already do this?

**Where they stand, 14 Oct:** three of the five are in 0.5.0, on the user's word ("will 0.5.0 have all the fixes?";
then "I agree your plan"): 3 curated training, 4 Rematch your loss, 5 Clock coach. Flagship 2 is 0.6, flagship 1 is
0.8. With them, 0.5.0 also brings the warm-up before you play on chess.com's home and the review one moment at a time
on chess.com's own board.

## The five flagships

### 1. Prep before a game
- **What it is:** a background check on your next opponent, whether a real player, a chess.com coach or a bot.
  - Where they play and which openings they choose.
  - What they lose to, and how to set up your pieces for an advantage.
- **Fair play:** strictly before the game starts and completely off once it begins. Check chess.com's fair-play rules before building it.

### 2. Voice, one to one
- **What it is:** talk with your coach by voice, about any game or move.
  - Example: "Review my game against X" goes move by move, out loud.
  - The coach answers from your whole history, not one game.
  - It needs the player's own free AI key. See ROADMAP, 0.6.

### 3. Curated training from your own games
- **What it is:** practice built from the positions where you went wrong, one habit at a time, at your level. Then "You vs you" proves whether the habit is fixed.
- **Status:** already in 0.5.0. The user liked it most in the test session, even with the bugs found.

### 4. Rematch your loss
- **What it is:** replay a game you lost, drew or stalemated, with the other side making exactly the moves they made in the real game.
  - At the moment it went wrong, you play something different.
  - From there, Stockfish plays on at your opponent's rating, and you learn to turn it around:
    - a loss into a win or a draw
    - a stalemate into a checkmate
    - a draw into a proper win
- **Where it lives:** in the Knightwise app.
  - The coach recommends it when it's needed, for example after a won position slipped away or after a stalemate.
- **Note:** chess.com doesn't share bot or coach games with apps, so those need another way in.
- **Status: in 0.5.0** (14 Oct). "Rematch from here" in the app's review, and "Rematch from move N" in Maya's review
  on chess.com. The engine picks among its best few moves with a spread that grows as the rating falls, and plays a
  loose move now and then. The page says plainly it's an approximation of a level, not the person.

### 5. Clock coach
- **What it is:** a coach for how you use your time.
  - chess.com's games record your clock on every move. Today Knightwise throws that away.
  - Use it to show where your time goes and where you rush.
  - Then train the right speed for each part of the game.
  - 14 of the user's losses were on time.
- **Status: in 0.5.0** (14 Oct), the first part: each game's review says how long you took on the move that cost the
  most, and your longest think; Progress says how many of your biggest mistakes in 30 games were played in a rush
  (19 of 48 for the user). Honest note: chess.com's own move list shows the time per move. What it doesn't do is
  tie the time to your mistakes and say what to change. Training the right speed is still to come.

## Normal features, not flagships
- **Stop-for-today guard:** between games only. After losses, when your games get faster and sloppier, the coach suggests a break.

More flagships can come later, one at a time.
