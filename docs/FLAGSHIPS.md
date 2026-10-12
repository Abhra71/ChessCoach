# Knightwise flagships

The rule, from 12 Oct 2026: every flagship is something chess.com does not have, and it's free.
A friend who plays on chess.com asked why anyone would use our practice and coach instead of chess.com's own.
"We have puzzles and reviews too" is not an answer. These are.

Build them one at a time after 0.5.0 ships. Before adding anything new, ask: does chess.com already do this?

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

### 5. Clock coach
- **What it is:** a coach for how you use your time.
  - chess.com's games record your clock on every move. Today Knightwise throws that away.
  - Use it to show where your time goes and where you rush.
  - Then train the right speed for each part of the game.
  - 14 of the user's losses were on time.

## Normal features, not flagships
- **Stop-for-today guard:** between games only. After losses, when your games get faster and sloppier, the coach suggests a break.

More flagships can come later, one at a time.
