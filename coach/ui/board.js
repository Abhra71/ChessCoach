// One chess board for the whole app: pieces, highlights, labelled arrows, clicks.
const Board = (() => {
  const FILES = "abcdefgh";
  const KIND = {  // what each arrow means, always written on the arrow too
    better: { color: "var(--better)", label: "Better" },
    mine: { color: "var(--mine)", label: "You played" },
    reply: { color: "var(--reply)", label: "Their best reply" },  // the engine's answer, not always what happened
    real: { color: "var(--real)", label: "They played" },  // what the opponent really played
  };

  function squares(fen) {  // "rnbqkbnr/pppppppp/..." -> { e1: "K", ... }
    const out = {}, rows = fen.split(" ")[0].split("/");
    rows.forEach((row, i) => {
      let f = 0;
      for (const c of row) {
        if (/\d/.test(c)) { f += Number(c); continue; }
        out[FILES[f] + (8 - i)] = c; f++;
      }
    });
    return out;
  }

  function xy(sq, flip) {
    const f = FILES.indexOf(sq[0]), r = Number(sq[1]) - 1;
    return [(flip ? 7 - f : f) * 10, (flip ? r : 7 - r) * 10];
  }

  function arrowSvg(a, flip) {
    const k = KIND[a.kind] || KIND.better;
    const [x1, y1] = xy(a.from, flip).map(v => v + 5), [x2, y2] = xy(a.to, flip).map(v => v + 5);
    const len = Math.hypot(x2 - x1, y2 - y1) || 1, ux = (x2 - x1) / len, uy = (y2 - y1) / len;
    const hx = x2 - ux * 3.6, hy = y2 - uy * 3.6, px = -uy * 2.2, py = ux * 2.2;
    const sx = x1 + ux * 2, sy = y1 + uy * 2;
    const tx = (sx + hx) / 2, ty = (sy + hy) / 2, text = a.label || k.label, w = text.length * 1.55 + 2.4;
    return `<g class="arrow" opacity=".92">
      <line x1="${sx}" y1="${sy}" x2="${hx}" y2="${hy}" stroke="${k.color}" stroke-width="1.7" stroke-linecap="round"/>
      <polygon points="${x2},${y2} ${hx + px},${hy + py} ${hx - px},${hy - py}" fill="${k.color}"/>
      <g class="tag"><rect x="${tx - w / 2}" y="${ty - 2.1}" width="${w}" height="4.2" fill="${k.color}"/>
      <text x="${tx}" y="${ty + 0.95}" text-anchor="middle">${text}</text></g></g>`;
  }

  // opts: { fen or pieces {sq: "K"}, flip, highlights: {sq: "hl-last"|...}, targets: [sq],
  //         arrows: [{from,to,kind,label}], onClick(sq) }
  function render(el, opts) {
    const flip = !!opts.flip, pieces = opts.pieces || squares(opts.fen), hl = opts.highlights || {};
    let s = `<svg class="board" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">`;
    for (let r = 0; r < 8; r++) for (let f = 0; f < 8; f++) {
      const sq = FILES[flip ? 7 - f : f] + (flip ? r + 1 : 8 - r);
      const light = (FILES.indexOf(sq[0]) + Number(sq[1])) % 2 === 1;
      s += `<rect data-sq="${sq}" x="${f * 10}" y="${r * 10}" width="10" height="10" class="${light ? "light" : "dark"}"/>`;
      if (hl[sq]) s += `<rect x="${f * 10}" y="${r * 10}" width="10" height="10" class="${hl[sq]}" pointer-events="none"/>`;
      if (f === 0) s += `<text x="${0.6}" y="${r * 10 + 3}" class="coord ${light ? "on-light" : "on-dark"}">${sq[1]}</text>`;
      if (r === 7) s += `<text x="${f * 10 + 8.3}" y="${79.3}" class="coord ${light ? "on-light" : "on-dark"}">${sq[0]}</text>`;
    }
    for (const t of opts.targets || []) {
      const [x, y] = xy(t, flip);
      s += `<circle cx="${x + 5}" cy="${y + 5}" r="1.6" class="target" pointer-events="none"/>`;
    }
    for (const [sq, p] of Object.entries(pieces)) {
      const [x, y] = xy(sq, flip);
      s += `<g data-p="${sq}"><g transform="translate(${x} ${y}) scale(${10 / 45})" pointer-events="none">${PIECES[p]}</g></g>`;
    }
    for (const a of opts.arrows || []) s += arrowSvg(a, flip);
    s += `</svg>`;
    el.innerHTML = s;
    slide(el, el._was, pieces, flip);
    el._was = { pieces: { ...pieces }, flip };
    if (opts.onClick) el.querySelectorAll("rect[data-sq]").forEach(r => r.onclick = () => opts.onClick(r.dataset.sq));
  }

  // a move slides instead of jumping: a piece that appeared on a square glides in from where the same piece left
  function slide(el, was, now, flip) {
    if (!was || was.flip !== flip || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const gone = Object.keys(was.pieces).filter(sq => was.pieces[sq] !== now[sq]);
    const came = Object.keys(now).filter(sq => was.pieces[sq] !== now[sq]);
    if (!came.length || came.length > 2 || gone.length > 3) return;  // a new position, not a move
    for (const to of came) {
      const from = gone.find(sq => was.pieces[sq] === now[to] && !now[sq]) || gone.find(sq => was.pieces[sq] === now[to]);
      const g = from && el.querySelector(`g[data-p="${to}"]`);
      if (!g || !g.animate) continue;
      const [x1, y1] = xy(from, flip), [x2, y2] = xy(to, flip);
      g.animate([{ transform: `translate(${x1 - x2}px, ${y1 - y2}px)` }, { transform: "translate(0, 0)" }],
        { duration: 190, easing: "cubic-bezier(.2,.7,.3,1)" });
    }
  }

  function legend(kinds) {
    return `<div class="legend">${kinds.map(k => `<span><i style="background:${KIND[k].color}"></i>${KIND[k].label}</span>`).join("")}</div>`;
  }

  return { render, squares, legend, KIND };
})();
