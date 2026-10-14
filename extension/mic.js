// One-time: Chrome asks whether the Knightwise extension may use the microphone (for Talk on chess.com, 0.6).
document.getElementById("allow").onclick = async () => {
  const state = document.getElementById("state");
  try {
    const s = await navigator.mediaDevices.getUserMedia({ audio: true });
    s.getTracks().forEach(t => t.stop());
    state.textContent = "Done. Close this tab and press Talk on Maya again.";
  } catch (e) {
    state.textContent = "Chrome didn't allow it. Click the microphone icon in the address bar to change that, then try again.";
  }
};
