// Pictures for the extension set-up: simple drawings of Chrome's screens, with the spot to click circled in red.
const Guide = (() => {
  const W = 520, H = 250;
  const frame = (inner, url) => `<svg viewBox="0 0 ${W} ${H}" class="shot" xmlns="http://www.w3.org/2000/svg">
    <rect x="0.5" y="0.5" width="${W - 1}" height="${H - 1}" rx="8" class="s-win"/>
    <rect x="0.5" y="0.5" width="${W - 1}" height="34" rx="8" class="s-bar"/><rect x="0.5" y="20" width="${W - 1}" height="15" class="s-bar"/>
    <circle cx="18" cy="17" r="4" class="s-dot"/><circle cx="32" cy="17" r="4" class="s-dot"/><circle cx="46" cy="17" r="4" class="s-dot"/>
    <rect x="64" y="8" width="${W - 84}" height="18" rx="9" class="s-url"/>
    <text x="78" y="21" class="s-urltext">${url}</text>${inner}</svg>`;
  const ring = (x, y, w, h) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${h / 2}" class="s-ring"/>`;
  const card = (x, y, title, sub) => `<rect x="${x}" y="${y}" width="150" height="62" rx="6" class="s-card"/>
    <rect x="${x + 10}" y="${y + 12}" width="18" height="18" rx="4" class="s-icon"/>
    <text x="${x + 36}" y="${y + 25}" class="s-title">${title}</text><text x="${x + 10}" y="${y + 48}" class="s-sub">${sub}</text>`;
  const page = (dev, loaded) => `
    <text x="20" y="62" class="s-h">Extensions</text>
    <text x="${W - 150}" y="62" class="s-sub">Developer mode</text>
    <rect x="${W - 54}" y="51" width="30" height="16" rx="8" class="${dev ? "s-on" : "s-off"}"/><circle cx="${dev ? W - 32 : W - 46}" cy="59" r="6" class="s-knob"/>
    ${dev ? `<rect x="20" y="78" width="104" height="24" rx="5" class="s-btn"/><text x="30" y="94" class="s-btntext">Load unpacked</text>
      <rect x="132" y="78" width="96" height="24" rx="5" class="s-btn2"/><text x="142" y="94" class="s-sub">Pack extension</text>` : ""}
    ${card(20, 118, "Some extension", "On")}${loaded ? card(184, 118, "Chess Coach", "Loaded from folder") : ""}`;
  const picker = `
    <rect x="40" y="48" width="${W - 80}" height="186" rx="6" class="s-card"/>
    <text x="54" y="68" class="s-title">Select the extension directory</text>
    <rect x="54" y="78" width="${W - 108}" height="20" rx="3" class="s-url"/><text x="62" y="92" class="s-urltext">C:\\Users\\you\\AppData\\Local\\Programs\\ChessCoach\\extension</text>
    <rect x="62" y="108" width="80" height="14" rx="2" class="s-btn2"/><text x="66" y="119" class="s-sub">background.js</text>
    <rect x="62" y="128" width="80" height="14" rx="2" class="s-btn2"/><text x="66" y="139" class="s-sub">manifest.json</text>
    <rect x="${W - 190}" y="200" width="90" height="22" rx="4" class="s-btn"/><text x="${W - 178}" y="215" class="s-btntext">Select Folder</text>
    <rect x="${W - 94}" y="200" width="48" height="22" rx="4" class="s-btn2"/><text x="${W - 86}" y="215" class="s-sub">Cancel</text>`;
  const steps = {
    open: frame(page(false, false) + ring(64, 4, W - 84, 26), "chrome://extensions"),
    dev: frame(page(false, false) + ring(W - 160, 46, 146, 26), "chrome://extensions"),
    load: frame(page(true, false) + ring(14, 73, 116, 34), "chrome://extensions"),
    pick: frame(picker + ring(48, 72, W - 96, 32) + ring(W - 196, 195, 102, 32), "chrome://extensions"),
    done: frame(page(true, true) + ring(178, 112, 162, 74), "chrome://extensions"),
  };
  return { steps };
})();
