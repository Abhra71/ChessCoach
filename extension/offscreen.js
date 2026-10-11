// Plays the coach's voice for chess.com pages: asks the Knightwise app for the sentence as audio, then plays it.
let audio = null;

const tell = on => chrome.runtime.sendMessage({ type: "speaking", on }).catch(() => {});

chrome.runtime.onMessage.addListener(msg => {
  if (msg.type === "stop" && audio) { audio.pause(); audio = null; tell(false); }
  if (msg.type !== "play") return;
  if (audio) { audio.pause(); audio = null; }
  fetch(msg.url, { method: "POST", headers: { "Content-Type": "application/json" },
                   body: JSON.stringify({ text: msg.text, voice: msg.voice }) })
    .then(r => { if (!r.ok) throw new Error("no voice"); return r.blob(); })
    .then(blob => {
      const a = new Audio(URL.createObjectURL(blob));
      audio = a;
      a.onplay = () => tell(true);
      a.onended = a.onerror = () => { if (audio === a) audio = null; tell(false); };
      return a.play();
    })
    .catch(() => tell(false));
});
