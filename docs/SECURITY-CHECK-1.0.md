# Security check, 23 Oct 2026 (before 1.0)

How Knightwise is built: a small server **only on this PC** (127.0.0.1:8765); the app window and the Chrome extension
talk to it. Tested by sending real attacks to it (`attack.py`, 25 checks) and by reading where data is kept.

## Passed
- Another website can't send commands or read anything (Origin check; no cross-site header). A sandboxed page
  (Origin: null) and chess.com's own page are refused too.
- A website pointing its own name at this PC (DNS rebinding) is refused (Host check).
- Plain form posts are refused (JSON only).
- No file outside the app can be read (6 path tricks: `..`, encoded, backslashes, a drive letter).
- Garbage: broken JSON, wrong shapes, wrong types, a non-number Content-Length, a client that lies about its
  length, a 60,000-character address, a 20 MB body: all answered or cut off, the server stays up.
- 600 requests at once: all answered after the fix below.
- AI keys: in Windows Credential Manager (encrypted for this Windows user); `settings.json` only says the provider;
  the app only ever shows the last 4 characters; no key-like string in any data file, logbook or the repo.
- The app page's own storage: only small preferences. The extension stores a version stamp, the fix list and
  "greeted" days; no keys, no personal data. Extension permissions: chess.com pages, the local server, storage,
  alarms, offscreen (sound). Nothing more.

## Fixed
- A JSON list (not an object) in a request raised an error inside the server (it stayed up). Now refused (400).
- Under a burst, a few connections were turned away (queue of 5). Queue raised to 64.

## From a real foreign website (example.com, in a browser)
All 7 tries blocked before reaching Knightwise: reading settings, reading games, commands (JSON, plain text, a blind
no-cors send), a 20 MB send, a path trick. Chrome itself refuses public sites talking to programs on this PC (Private
Network Access); Knightwise's own Origin and Host checks are the second lock (tested above by script).

## Chaos test (Gremlins.js 2.2.0, in a test tab only)
Every app page (25), 700 to 1,200 random clicks, typing, scrolling and form-filling each; a safety net in that tab
kept anything that sends, deletes or opens windows from leaving it. No crash, no freeze. One real bug, 7 times: a page
that finished loading (or a practice reply that came back) after you'd moved on tried to draw on a page that was gone;
Settings could even redraw itself over another page. Fixed: the router draws the page you're on again when a slower
one finishes late; the practice board and Settings check they're still there. Re-run on the same pages: 0 errors.
Never run on chess.com (random clicks there could start or resign a real game).

## Known, for 1.1
- Any installed Chrome extension (not only Knightwise's) may talk to the server. A harmful extension could already do
  much worse inside the browser, so the risk is low; the fix is to allow only Knightwise's own extension ID.

## Found on this PC
- The old Knightwise **0.4.1** (early Store test) is still installed. It starts with Windows and has looser rules
  (it answers any website). At 23:18 the test copy stopped and 0.4.1 took its place. Uninstall 0.4.1
  (Settings > Apps) before testing the 1.0 package; installing 1.0 from the Store replaces it anyway.
