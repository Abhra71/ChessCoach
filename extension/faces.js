// The four Knightwise coaches, drawn in code (flat cartoon, original characters). Each face has four moods
// (pleased, calm, worried, thinking), blinks by itself and moves its mouth while it talks (see coach.css).
// KnightwiseFaces.svg(coach, mood) -> an <svg> string.
(() => {
  const LOOK = {
    maya: {  // former champion, about 35: brown skin, black hair in a bun, navy blazer, small earrings
      skin: "#A86F4C", shade: "#8E5B3C", hair: "#1E1613", top: "#22324F", collar: "#F2EEE6", lips: "#7A3E2E",
      back: `<circle cx="60" cy="24" r="12" fill="HAIR"/>`,
      front: `<path d="M33 55 C31 33 46 24 60 24 C76 24 89 34 87 55 C84 44 76 37 60 37 C47 37 38 43 33 55Z" fill="HAIR"/>`,
      extra: `<circle cx="33.5" cy="66" r="2.2" fill="#E8C766"/><circle cx="86.5" cy="66" r="2.2" fill="#E8C766"/>`,
      clothes: `<path d="M50 96 L60 108 L70 96 Z" fill="COLLAR"/>`,
    },
    arjun: {  // young prodigy, about 19: light-brown skin, short wavy black hair, orange hoodie
      skin: "#C89067", shade: "#AD7652", hair: "#16110F", top: "#E8743B", collar: "#C85E2A", lips: "#8A4E3A",
      back: "",
      front: `<path d="M34 54 C30 30 50 22 62 24 C72 22 90 30 86 52 C84 44 80 40 74 39 C70 33 64 36 60 33 C55 38 48 35 44 40 C39 42 35 47 34 54Z" fill="HAIR"/>`,
      extra: "",
      clothes: `<path d="M44 94 C48 104 72 104 76 94" stroke="COLLAR" stroke-width="4" fill="none"/><line x1="54" y1="100" x2="53" y2="112" stroke="#F6F1EA" stroke-width="2"/><line x1="66" y1="100" x2="67" y2="112" stroke="#F6F1EA" stroke-width="2"/>`,
    },
    zara: {  // attacking player, about 22: fair skin with freckles, auburn ponytail, green jacket
      skin: "#F0C7A6", shade: "#DDAA87", hair: "#9C3D1F", top: "#2E7D5B", collar: "#1F5C42", lips: "#B5534A",
      back: `<path d="M84 44 C98 50 98 74 90 86 C96 70 90 58 82 54Z" fill="HAIR"/>`,
      front: `<path d="M33 58 C30 32 46 24 62 25 C78 26 90 36 87 56 C80 42 68 36 52 40 C44 43 37 49 33 58Z" fill="HAIR"/>`,
      extra: `<g fill="#C98563" opacity=".7"><circle cx="45" cy="68" r=".9"/><circle cx="48.5" cy="70" r=".9"/><circle cx="44" cy="71.5" r=".9"/><circle cx="75" cy="68" r=".9"/><circle cx="71.5" cy="70" r=".9"/><circle cx="76" cy="71.5" r=".9"/></g>`,
      clothes: `<path d="M50 95 L60 104 L70 95" stroke="COLLAR" stroke-width="5" fill="none"/>`,
    },
    viktor: {  // veteran, about 60: light skin, grey hair and beard, round glasses, brown cardigan
      skin: "#E9C2A0", shade: "#D3A783", hair: "#B9B6B1", top: "#6B4A33", collar: "#E9E4DA", lips: "#9A5A4A",
      back: "",
      front: `<path d="M33 60 C31 46 33 38 38 34 C38 42 40 46 41 50 C40 44 41 40 44 37 M87 60 C89 46 87 38 82 34 C82 42 80 46 79 50 C80 44 79 40 76 37" fill="HAIR" stroke="HAIR" stroke-width="3"/>`,
      extra: `<path d="M38 70 C40 92 50 98 60 98 C70 98 80 92 82 70 C78 82 70 84 60 84 C50 84 42 82 38 70Z" fill="HAIR"/>
        <g fill="none" stroke="#3B3B3B" stroke-width="1.8"><circle cx="49" cy="59" r="7"/><circle cx="71" cy="59" r="7"/><path d="M56 59 Q60 56 64 59"/></g>`,
      clothes: `<path d="M50 96 L60 110 L70 96 Z" fill="COLLAR"/><circle cx="60" cy="114" r="1.5" fill="#3A2718"/>`,
    },
  };

  const BROWS = {
    pleased: ["M43 48 Q49 44 55 47", "M65 47 Q71 44 77 48"],
    calm: ["M43 49 Q49 47 55 49", "M65 49 Q71 47 77 49"],
    worried: ["M43 51 Q49 49 55 46", "M65 46 Q71 49 77 51"],
    thinking: ["M43 46 Q49 42 55 45", "M65 50 Q71 49 77 50"],
  };
  const MOUTH = {
    pleased: `<path d="M50 73 Q60 84 70 73 Z" fill="#5A2A22"/><path d="M52 74 Q60 77 68 74" stroke="#fff" stroke-width="2.2" fill="none"/>`,
    calm: `<path d="M52 75 Q60 80 68 75" stroke="LIPS" stroke-width="2.6" stroke-linecap="round" fill="none"/>`,
    worried: `<path d="M53 78 Q60 73 67 78" stroke="LIPS" stroke-width="2.6" stroke-linecap="round" fill="none"/>`,
    thinking: `<path d="M54 76 Q60 76 66 74" stroke="LIPS" stroke-width="2.6" stroke-linecap="round" fill="none"/>`,
  };

  function eyes(mood) {
    if (mood === "pleased") {
      return `<g class="kw-eyes" stroke="#2A1D18" stroke-width="2.6" stroke-linecap="round" fill="none">
        <path d="M45 60 Q49 55 53 60"/><path d="M67 60 Q71 55 75 60"/></g>`;
    }
    const dx = mood === "thinking" ? -1.4 : 0, dy = mood === "thinking" ? -1.6 : 0;
    return `<g class="kw-eyes"><ellipse cx="49" cy="59" rx="4.2" ry="4.6" fill="#fff"/><ellipse cx="71" cy="59" rx="4.2" ry="4.6" fill="#fff"/>
      <circle cx="${49 + dx}" cy="${59.5 + dy}" r="2.6" fill="#2A1D18"/><circle cx="${71 + dx}" cy="${59.5 + dy}" r="2.6" fill="#2A1D18"/>
      <circle cx="${50 + dx}" cy="${58.4 + dy}" r=".8" fill="#fff"/><circle cx="${72 + dx}" cy="${58.4 + dy}" r=".8" fill="#fff"/></g>`;
  }

  function svg(coach, mood = "calm") {
    const L = LOOK[coach] || LOOK.zara;
    mood = BROWS[mood] ? mood : "calm";
    const fill = s => s.replace(/HAIR/g, L.hair).replace(/COLLAR/g, L.collar).replace(/LIPS/g, L.lips);
    return `<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" class="kw-face kw-${coach} kw-${mood}" role="img" aria-label="${coach}">
      <circle cx="60" cy="60" r="60" fill="#14161A"/>
      <clipPath id="kw-clip-${coach}"><circle cx="60" cy="60" r="60"/></clipPath>
      <g clip-path="url(#kw-clip-${coach})">
        <path d="M14 124 C16 102 34 92 60 92 C86 92 104 102 106 124Z" fill="${L.top}"/>
        ${fill(L.clothes)}
        <rect x="52" y="80" width="16" height="16" rx="6" fill="${L.shade}"/>
        ${fill(L.back)}
        <ellipse cx="33" cy="62" rx="4" ry="6" fill="${L.shade}"/><ellipse cx="87" cy="62" rx="4" ry="6" fill="${L.shade}"/>
        <ellipse cx="60" cy="60" rx="26" ry="29" fill="${L.skin}"/>
        ${fill(L.front)}
        <g stroke="${L.hair === "#B9B6B1" ? "#8E8A84" : L.hair}" stroke-width="2.4" stroke-linecap="round" fill="none">
          <path d="${BROWS[mood][0]}"/><path d="${BROWS[mood][1]}"/></g>
        ${eyes(mood)}
        <path d="M60 62 Q57 69 60 70 Q62 70 63 69" stroke="${L.shade}" stroke-width="2" fill="none" stroke-linecap="round"/>
        <g class="kw-mouth">${fill(MOUTH[mood])}</g>
        <ellipse class="kw-talk" cx="60" cy="76" rx="5.5" ry="4" fill="#5A2A22"/>
        ${fill(L.extra)}
      </g></svg>`;
  }

  window.KnightwiseFaces = { svg, coaches: Object.keys(LOOK), moods: Object.keys(BROWS) };
})();
