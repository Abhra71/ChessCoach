// Your game of the week as a short 3D film (1.0), on the welcome film's antique set (Poly Haven, CC0).
// Readable on purpose: seen from your side of the board, high up like a broadcast; quiet moves go by quickly, the
// moves that won it slow down with a caption and the camera leans in, then back up. Captions are drawn into the
// picture itself, so the saved video is exactly what was on screen. The script comes from coach/film.py.
// The scene's set-up is the same as backdrop.js (the welcome), kept apart so the welcome can't break because of this.
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const SQUARE = 0.058, EDGE = -0.203;  // the model's board: a1 at (-0.203, -0.203), 5.8 cm squares
const FILES = "abcdefgh";
const at = sq => new THREE.Vector3(EDGE + FILES.indexOf(sq[0]) * SQUARE, 0.017, EDGE + (Number(sq[1]) - 1) * SQUARE);
const KIND = { p: "pawn", n: "knight", b: "bishop", r: "rook", q: "queen", k: "king" };

// music: the track's address (or null). Its loudness follows the film: in with the title, steady under the moves,
// a little lower under a caption, up for the last winning move, out with the end card. It's in the saved video too.
// 20 Oct, the owner: the songs are good "but that loud though": about 40% lower than first set
const LOUD = { intro: 0.32, moves: 0.32, caption: 0.24, last: 0.45, end: 0 };

function play(el, script, { record = false, music = null, onEnd = () => {} } = {}) {
  const W = 1280, H = 720;  // the film's own size: the same on every screen and in the saved video
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(1);
  renderer.setSize(W, H, false);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.85;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  const out = document.createElement("canvas");  // what you see and what is saved: the scene plus its words
  out.width = W; out.height = H;
  out.style.cssText = "width:100%;height:auto;display:block;border-radius:10px;background:#050505";
  el.innerHTML = ""; el.appendChild(out);
  const ctx = out.getContext("2d");

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x050505);
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.45;
  const camera = new THREE.PerspectiveCamera(34, W / H, 0.01, 10);
  const key = new THREE.SpotLight(0xfff1dc, 9, 2.5, Math.PI / 6, 0.55, 1.6);
  key.position.set(0.3, 0.8, 0.2);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.bias = -0.0004;
  scene.add(key, key.target);
  const rim = new THREE.DirectionalLight(0x9fb4ff, 0.6);
  rim.position.set(-0.6, 0.4, -0.5);
  scene.add(rim);

  // squares that light up: the last move (amber) and a winning move (green)
  const mark = color => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(SQUARE, SQUARE),
      new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.38, depthWrite: false }));
    m.rotation.x = -Math.PI / 2; m.visible = false; scene.add(m); return m;
  };
  const lastFrom = mark(0xf0a43a), lastTo = mark(0xf0a43a), win = mark(0x36c27a);
  const place = (m, sq) => { const p = at(sq); m.position.set(p.x, 0.0178, p.z); m.visible = true; };

  const you = script.you === "black" ? -1 : 1;  // the camera sits on your side of the board
  const pieces = {}, models = {};
  let ready = false;
  new GLTFLoader().load("/ui/vendor/chess_set/chess_set_2k.gltf", gltf => {
    gltf.scene.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    scene.add(gltf.scene);
    for (const o of [...gltf.scene.children]) {
      if (!o.name.startsWith("piece_")) continue;
      const f = Math.round((o.position.x - EDGE) / SQUARE), r = Math.round((o.position.z - EDGE) / SQUARE);
      pieces[FILES[f] + (r + 1)] = o;
      const [, kind, color] = o.name.split("_");
      models[`${kind}_${color}`] = models[`${kind}_${color}`] || o;  // a model of each piece, for promotions
    }
    ready = true;
  }, undefined, () => { ended = true; onEnd({ error: "The 3D set couldn't load." }); });

  // the broadcast view: high above your side, the whole board in the picture, drifting very slightly
  const wide = t => new THREE.Vector3(Math.sin(t * 0.05) * 0.04, 0.66, -0.5 * you);
  const centre = new THREE.Vector3(0, 0, -0.02 * you);
  const eye = wide(0), aim = centre.clone(), focus = new THREE.Vector3();
  let lean = 0;  // 0 = the broadcast view, 1 = leaning in on a winning move

  const steps = script.moves;
  let i = 0, phase = "intro", t = 0, moving = null, caption = null, ended = false, total = 0;
  const INTRO = 2.6, ENDING = 4.5;
  function begin(s) {
    const piece = pieces[s.from];
    if (!piece) return null;
    const slow = !!s.slow;
    const jobs = [{ obj: piece, from: at(s.from), to: at(s.to), lift: piece.name.includes("knight") ? 0.085 : 0.045 }];
    if (s.rook && pieces[s.rook[0]]) jobs.push({ obj: pieces[s.rook[0]], from: at(s.rook[0]), to: at(s.rook[1]), lift: 0.03 });
    const taken = s.capture ? pieces[s.capture] : null;
    delete pieces[s.from];
    if (s.capture) delete pieces[s.capture];
    pieces[s.to] = piece;
    if (s.rook && pieces[s.rook[0]]) { pieces[s.rook[1]] = pieces[s.rook[0]]; delete pieces[s.rook[0]]; }
    place(lastFrom, s.from); place(lastTo, s.to);
    win.visible = false;
    if (slow) { place(win, s.to); lastTo.visible = false; focus.copy(at(s.to)); caption = s.caption; }
    return { s, jobs, taken, t: 0, length: slow ? 1.5 : Math.max(0.25, script.quiet * 0.7),
             hold: slow ? 2.8 : script.quiet * 0.3 };
  }
  function promote(s) {
    const color = Number(s.to[1]) === 8 ? "white" : "black", model = models[`${KIND[s.promo]}_${color}`];
    if (!model) return;
    const pawn = pieces[s.to], piece = model.clone();
    pawn.visible = false;
    piece.position.copy(at(s.to)); piece.visible = true; piece.scale.setScalar(1);
    scene.add(piece);
    pieces[s.to] = piece;
  }

  function words() {  // the film's words, drawn on the picture
    // the 3D set is built as a mirror image (its queens stand on the kings' side: piece_queen_white is at d1 by
    // its squares but on the king's side in the picture), so the picture is flipped left to right first: then the
    // board is the right way round, and the words, drawn after, read normally (20 Oct)
    ctx.save(); ctx.translate(W, 0); ctx.scale(-1, 1);
    ctx.drawImage(renderer.domElement, 0, 0);
    ctx.restore();
    ctx.textBaseline = "middle";
    const white = script.white, black = script.black;
    ctx.fillStyle = "rgba(0,0,0,.45)"; ctx.fillRect(0, 0, W, 54);
    ctx.fillStyle = "#f2f2f2"; ctx.font = "600 22px 'Segoe UI', system-ui, sans-serif";
    ctx.fillText(`${white} (White)  vs  ${black} (Black)`, 28, 28);
    ctx.textAlign = "right"; ctx.fillStyle = "#9a9a9a"; ctx.font = "500 18px 'Segoe UI', system-ui, sans-serif";
    ctx.fillText(phase === "moves" || phase === "hold" ? `move ${Math.floor(i / 2) + 1}` : script.date, W - 28, 28);
    ctx.textAlign = "left";
    if (caption) {
      ctx.font = "600 34px 'Segoe UI', system-ui, sans-serif";
      const w = ctx.measureText(caption).width + 60;
      ctx.fillStyle = "rgba(10,10,10,.82)"; roundRect((W - w) / 2, H - 112, w, 64, 12);
      ctx.fillStyle = "#36c27a"; ctx.fillRect((W - w) / 2, H - 112, 6, 64);
      ctx.fillStyle = "#ffffff"; ctx.textAlign = "center"; ctx.fillText(caption, W / 2, H - 80); ctx.textAlign = "left";
    }
    if (phase === "intro" || phase === "end") {
      const k = phase === "intro" ? Math.max(0, 1 - Math.max(0, t - INTRO + 0.8) / 0.8) : Math.min(1, t / 0.8);
      ctx.fillStyle = `rgba(5,5,5,${0.72 * k})`; ctx.fillRect(0, 0, W, H);
      ctx.globalAlpha = k; ctx.textAlign = "center"; ctx.fillStyle = "#ffffff";
      ctx.font = "700 54px 'Segoe UI', system-ui, sans-serif";
      ctx.fillText(phase === "intro" ? script.title : script.end, W / 2, H / 2 - 30);
      ctx.font = "500 26px 'Segoe UI', system-ui, sans-serif"; ctx.fillStyle = "#cfcfcf";
      ctx.fillText(phase === "intro" ? `against ${script.opponent} · ${script.date}` : "Made with Knightwise · free chess coaching", W / 2, H / 2 + 34);
      ctx.globalAlpha = 1; ctx.textAlign = "left";
    }
  }
  function roundRect(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); ctx.fill(); }

  let track = null, gain = null, actx = null, toTape = null;
  if (music) {
    try {
      track = new Audio(music); track.loop = true;
      actx = new AudioContext();
      gain = actx.createGain(); gain.gain.value = 0;
      actx.createMediaElementSource(track).connect(gain);
      gain.connect(actx.destination);
      if (record) { toTape = actx.createMediaStreamDestination(); gain.connect(toTape); }
      track.onerror = () => { track = null; };  // no music file: the film plays on in silence
      track.play().catch(() => {});
    } catch (e) { track = null; }
  }
  const lastSlow = steps.reduce((k, s, n) => (s.slow ? n : k), -1);
  function loudness(dt) {
    if (!gain) return;
    const want = phase === "intro" ? LOUD.intro * Math.min(1, t / INTRO) : phase === "end" ? LOUD.end
      : moving && moving.s.slow ? (i - 1 === lastSlow ? LOUD.last : LOUD.caption) : LOUD.moves;
    gain.gain.value += (want - gain.gain.value) * (1 - Math.exp(-dt * (phase === "end" ? 0.9 : 2.2)));
  }

  let recorder = null, chunks = [];
  if (record && window.MediaRecorder) {
    const sound = toTape ? toTape.stream.getAudioTracks() : [];
    const type = (sound.length ? ["video/webm;codecs=vp9,opus", "video/webm;codecs=vp8,opus"] : [])
      .concat(["video/webm;codecs=vp9", "video/webm;codecs=vp8", "video/webm"]).find(m => MediaRecorder.isTypeSupported(m));
    if (type) {
      const stream = new MediaStream([...out.captureStream(30).getVideoTracks(), ...(type.includes("opus") ? sound : [])]);
      recorder = new MediaRecorder(stream, { mimeType: type, videoBitsPerSecond: 6000000 });
      recorder.ondataavailable = e => { if (e.data.size) chunks.push(e.data); };
    }
  }
  const quiet = () => { if (track) track.pause(); if (actx) actx.close().catch(() => {}); };

  const clock = new THREE.Clock();
  let alive = true;
  function frame() {
    if (!alive) return;
    requestAnimationFrame(frame);
    tick(Math.min(clock.getDelta(), 0.1));  // a slow PC drops frames but keeps time (a tenth of a second at most per frame)
  }
  function tick(dt) {  // the film moves on by dt seconds, and is drawn
    total += dt;
    if (ready && !ended) {
      if (recorder && recorder.state === "inactive") recorder.start(250);
      t += dt;
      if (phase === "intro" && t >= INTRO) { phase = "moves"; t = 0; }
      if (phase === "moves" && !moving) {
        if (i >= steps.length) { phase = "end"; t = 0; caption = null; }
        else { moving = begin(steps[i++]); if (!moving) i = steps.length; t = 0; }
      }
      if (moving) {
        moving.t += dt;
        const k = Math.min(1, moving.t / moving.length), e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
        for (const j of moving.jobs) {
          j.obj.position.lerpVectors(j.from, j.to, e);
          j.obj.position.y = 0.017 + Math.sin(Math.PI * e) * j.lift;
        }
        if (moving.taken) { moving.taken.scale.setScalar(Math.max(0.001, 1 - e)); if (k >= 1) moving.taken.visible = false; }
        if (k >= 1 && moving.s.promo && !moving.promoted) { promote(moving.s); moving.promoted = true; }
        if (moving.t >= moving.length + moving.hold) { if (moving.s.slow) caption = null; moving = null; }
      }
      loudness(dt);
      if (phase === "end" && t >= ENDING) {
        ended = true;
        if (recorder && recorder.state === "recording") {
          recorder.onstop = () => { quiet(); onEnd({ video: new Blob(chunks, { type: recorder.mimeType }) }); };
          recorder.stop();
        } else { quiet(); onEnd({}); }
      }
    }
    // the camera: broadcast, leaning in on a winning move while its caption shows
    const target = moving && moving.s.slow ? 1 : 0;
    lean += (target - lean) * (1 - Math.exp(-dt * 1.6));
    const close = focus.clone().add(new THREE.Vector3(0.05, 0.26, -0.24 * you));
    eye.copy(wide(total).lerp(close, lean * 0.75));
    aim.copy(centre.clone().lerp(focus.clone().setY(0.02), lean * 0.85));
    camera.position.copy(eye);
    camera.lookAt(aim);
    renderer.render(scene, camera);
    words();
  }
  frame();
  const stop = () => { alive = false; if (recorder && recorder.state === "recording") recorder.stop(); quiet(); renderer.dispose(); };
  // step(seconds): jump the film on, for screenshots and checks (a hidden window draws almost no frames)
  stop.step = seconds => { for (let k = 0; k < seconds / 0.05; k++) tick(0.05); };
  return stop;
}

window.Film = { play };
window.dispatchEvent(new Event("film-ready"));
