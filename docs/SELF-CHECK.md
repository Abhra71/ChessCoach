# The chess.com self-check

chess.com changes its site without notice. On 13 Oct 2026, live games moved from `/game/live/<id>` to `/game/<id>`
and `/live/game/<id>`, and Maya's review silently stopped appearing. The self-check exists so that the next change
is **noticed, named and survivable**, even when nobody is working on Knightwise.

## How it works
1. **One list of everything we read from chess.com:** [extension/contract.js](../extension/contract.js).
   - Game addresses, the board element and its older names, the piece classes, the move list, the players' names.
   - The page scripts use only this file.
2. **A check wherever it's used.**
   - On chess.com, the extension reports each check to the app as found or not found: `game-address`, `board`, `pieces`, `player-names`, `move-list`.
   - A game page at an address we don't know (a board, plus a long number in the address) is reported, never acted on.
   - On every download, the app checks the public API's answer: `api-archives` and `api-games`.
3. **Fail gracefully.** A broken check pauses only its feature.
   - With no board or no pieces, Maya still lists the moments, says why there are no arrows, and offers "Open this review in Knightwise".
   - If chess.com's API changes shape, the last good copy of your games is kept. No internet on the PC is never blamed on chess.com.
4. **Visible health.**
   - Settings has a "chess.com check" row: all working with the time it was last verified, or what broke and since when.
   - The extension pop-up shows the same in one line.
   - The record is in `data/health.json`, managed by [coach/health.py](../coach/health.py).
5. **An alarm while you're away.**
   - [.github/workflows/chesscom-check.yml](../.github/workflows/chesscom-check.yml) runs every Monday.
   - It checks the public API live and runs the contract tests. On failure it opens a GitHub issue, and GitHub emails the owner.
   - It doesn't visit chess.com's pages from a server, which may break chess.com's rules. Pages are checked in the player's own browser.

## Fair play stays the same
- The coach only appears on allow-listed sections: home, puzzles, lessons, stats and archive.
- The review only shows for games the app knows, which means archived and finished.
- Both scripts load on every chess.com page, because chess.com changes pages without reloading. They decide in code when to act, and on a live game they show nothing and read no position.

## When the alarm goes off, or Settings shows red
1. **Open a finished game** on chess.com and look at what changed. Use the browser's inspector, or ask Claude with Claude in Chrome once the game is over.
2. **Update [contract.js](../extension/contract.js):**
   - Add the new address or element name as the first entry.
   - Keep the old ones as backups.
3. **Save a new trimmed copy** of the game page as `tests/fixtures/chesscom-game-<date>.html`:
   - Only the board and its pieces, the first move-list nodes and the names.
   - Replace the opponent's name.
   - Point [tests/test_contract.py](../tests/test_contract.py) at it, with that game's final position.
4. **Run the tests,** then publish a new extension version with the app.
