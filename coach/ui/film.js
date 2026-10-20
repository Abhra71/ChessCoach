// Your game of the week as a short 3D film (1.0), on the welcome film's antique set (Poly Haven, CC0).
// Readable on purpose (20 Oct, the owner): mostly seen from above, the whole board in the picture, with one to
// three close shots, each from its own angle, on the moves that won it. Quiet moves go by at an easy pace; the
// winning ones slow down with a caption. The music is placed so its main part arrives with the first winning move,
// its build-up before. Pause, and a still preview before it starts. Captions are drawn into the picture itself, so
// the saved video is exactly what was on screen. The script comes from coach/film.py.
// The scene's set-up is the same as backdrop.js (the welcome), kept apart so the welcome can't break because of this.
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const SQUARE = 0.058, EDGE = -0.203;  // the model's board: a1 at (-0.203, -0.203), 5.8 cm squares
const FILES = "abcdefgh";
const at = sq => new THREE.Vector3(EDGE + FILES.indexOf(sq[0]) * SQUARE, 0.017, EDGE + (Number(sq[1]) - 1) * SQUARE);
const KIND = { p: "pawn", n: "knight", b: "bishop", r: "rook", q: "queen", k: "king" };

// The music's loudness follows the film: up as it comes in, steady under the moves, a little lower under a caption,
// up for the last winning move, out with the end card. 20 Oct, the owner: good songs "but that loud though".
const LOUD = { moves: 0.32, caption: 0.24, last: 0.45, end: 0 };
const INTRO = 2.6, ENDING = 4.5;
const SLOW = { length: 1.9, hold: 3.4 };  // a winning move: played slowly, then held with its caption
const CLOSE_SHOTS = 3;  // close shots at most: the last winning move and the two before it
const MUSIC_WAIT = 12;  // the film may begin quiet for this long, so the song's build-up leads into the first close shot

const quietStep = q => ({ length: Math.max(0.35, q * 0.7), hold: q * 0.3 });

// When each step starts in the film, in seconds (the same sums the film makes as it plays)
function timeline(script) {
  let t = INTRO;
  return script.moves.map(s => { const at = t, d = s.slow ? SLOW : quietStep(script.quiet); t += d.length + d.hold; return at; });
}

// music: {url, peak} (peak: the second the song's main part starts) or null.
// autoplay false: a still preview (the board and the title card) until resume().
function play(el, script, { record = false, music = null, autoplay = true, onEnd = () => {} } = {}) {
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

  // The camera. From above: the whole board, tilted a little towards your side so the pieces stand up, drifting
  // very slightly. Close: low beside the piece that moved, each close shot from its own angle.
  const above = t => new THREE.Vector3(Math.sin(t * 0.04) * 0.02, 1.2, -0.24 * you);  // high enough for all eight ranks
  const centre = new THREE.Vector3(0, 0, 0);
  const ANGLES = [  // offsets from the piece, in your side's direction; high enough to look over the pieces in front
    t => new THREE.Vector3(0.16, 0.17, -0.18 * you),
    t => new THREE.Vector3(-0.17, 0.18, -0.15 * you),
    t => { const a = 0.6 + t * 0.12; return new THREE.Vector3(Math.cos(a) * 0.21, 0.19, -Math.sin(a) * 0.21 * you); },  // a slow orbit
  ];
  const eye = above(0), aim = centre.clone(), focus = new THREE.Vector3();
  let lean = 0, angle = 0;  // lean: 0 = from above, 1 = close

  const steps = script.moves;
  const starts = timeline(script);
  const slowAt = steps.map((s, n) => (s.slow ? n : -1)).filter(n => n >= 0);
  const closeAt = new Set(slowAt.slice(-CLOSE_SHOTS));  // the last winning moves get the close shots
  const lastSlow = slowAt.length ? slowAt[slowAt.length - 1] : -1;
  let i = 0, phase = "intro", t = 0, moving = null, caption = null, ended = false, total = 0, filmT = 0, closeCount = 0;
  function begin(s, n) {
    const piece = pieces[s.from];
    if (!piece) return null;
    const slow = !!s.slow, d = slow ? SLOW : quietStep(script.quiet);
    const jobs = [{ obj: piece, from: at(s.from), to: at(s.to), lift: piece.name.includes("knight") ? 0.085 : 0.045 }];
    if (s.rook && pieces[s.rook[0]]) jobs.push({ obj: pieces[s.rook[0]], from: at(s.rook[0]), to: at(s.rook[1]), lift: 0.03 });
    const taken = s.capture ? pieces[s.capture] : null;
    delete pieces[s.from];
    if (s.capture) delete pieces[s.capture];
    pieces[s.to] = piece;
    if (s.rook && pieces[s.rook[0]]) { pieces[s.rook[1]] = pieces[s.rook[0]]; delete pieces[s.rook[0]]; }
    place(lastFrom, s.from); place(lastTo, s.to);
    win.visible = false;
    const close = closeAt.has(n);
    if (slow) { place(win, s.to); lastTo.visible = false; focus.copy(at(s.to)); caption = s.caption; }
    if (close) angle = closeCount++ % ANGLES.length;
    return { s, n, jobs, taken, t: 0, close, length: d.length, hold: d.hold };
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
    ctx.fillStyle = "rgba(0,0,0,.45)"; ctx.fillRect(0, 0, W, 54);
    ctx.fillStyle = "#f2f2f2"; ctx.font = "600 22px 'Segoe UI', system-ui, sans-serif";
    ctx.fillText(`${script.white} (White)  vs  ${script.black} (Black)`, 28, 28);
    ctx.textAlign = "right"; ctx.fillStyle = "#9a9a9a"; ctx.font = "500 18px 'Segoe UI', system-ui, sans-serif";
    ctx.fillText(phase === "moves" ? `move ${Math.floor(i / 2) + 1}` : script.date, W - 28, 28);
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
    if (paused && !started) {  // the preview: a play sign over the still
      ctx.fillStyle = "rgba(255,255,255,.9)"; ctx.beginPath(); ctx.arc(W / 2, H / 2 + 130, 44, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = "#0a0a0a"; ctx.beginPath(); ctx.moveTo(W / 2 - 12, H / 2 + 108); ctx.lineTo(W / 2 + 22, H / 2 + 130);
      ctx.lineTo(W / 2 - 12, H / 2 + 152); ctx.fill();
    }
  }
  function roundRect(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); ctx.fill(); }

  // The music, placed: its main part (music.peak) arrives with the first close shot, the build-up before it. The
  // film may start quiet for up to MUSIC_WAIT seconds for that; for a long game the song starts further in instead.
  let track = null, gain = null, actx = null, toTape = null, musicAt = 0, musicFrom = 0, musicOn = false;
  if (music && music.url) {
    try {
      track = new Audio(music.url); track.loop = true; track.preload = "auto";
      actx = new AudioContext();
      gain = actx.createGain(); gain.gain.value = 0;
      actx.createMediaElementSource(track).connect(gain);
      gain.connect(actx.destination);
      if (record) { toTape = actx.createMediaStreamDestination(); gain.connect(toTape); }
      track.onerror = () => { track = null; };  // no music file: the film plays on in silence
      const firstClose = [...closeAt].sort((a, b) => a - b)[0];
      const keyAt = firstClose != null ? starts[firstClose] : INTRO;
      const peak = music.peak || 0;
      musicAt = Math.min(MUSIC_WAIT, Math.max(0, keyAt - peak));  // when, in the film, the song starts
      musicFrom = Math.max(0, peak - (keyAt - musicAt));  // and from where in the song
    } catch (e) { track = null; }
  }
  function loudness(dt) {
    if (!gain) return;
    const want = phase === "end" ? LOUD.end : !musicOn ? 0
      : moving && moving.s.slow ? (moving.n === lastSlow ? LOUD.last : LOUD.caption) : LOUD.moves;
    gain.gain.value += (want - gain.gain.value) * (1 - Math.exp(-dt * (phase === "end" ? 0.9 : 1.6)));
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
  let alive = true, paused = !autoplay, started = autoplay;
  function frame() {
    if (!alive) return;
    requestAnimationFrame(frame);
    const dt = Math.min(clock.getDelta(), 0.1);  // a slow PC drops frames but keeps time (a tenth of a second at most per frame)
    if (paused) draw(0); else tick(dt);
  }
  function tick(dt) {  // the film moves on by dt seconds, and is drawn
    total += dt;
    if (ready && !ended) {
      if (recorder && recorder.state === "inactive") recorder.start(250);
      t += dt; filmT += dt;
      if (track && !musicOn && filmT >= musicAt) {  // the song comes in, from its chosen point
        musicOn = true;
        try { track.currentTime = musicFrom; } catch (e) {}
        if (actx.state === "suspended") actx.resume().catch(() => {});
        track.play().catch(() => {});
      }
      if (phase === "intro" && t >= INTRO) { phase = "moves"; t = 0; }
      if (phase === "moves" && !moving) {
        if (i >= steps.length) { phase = "end"; t = 0; caption = null; }
        else { moving = begin(steps[i], i); i++; if (!moving) i = steps.length; t = 0; }
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
    draw(dt);
  }
  function draw(dt) {  // the camera, from above or close on a winning move, then the picture and its words
    const target = moving && moving.close ? 1 : 0;
    lean += (target - lean) * (1 - Math.exp(-dt * 1.4));
    const close = focus.clone().add(ANGLES[angle](moving ? moving.t : 0));
    eye.copy(above(total).lerp(close, lean));
    aim.copy(centre.clone().lerp(focus.clone().setY(0.02), lean));
    camera.position.copy(eye);
    camera.lookAt(aim);
    renderer.render(scene, camera);
    words();
  }
  frame();
  const stop = () => { alive = false; if (recorder && recorder.state !== "inactive") recorder.stop(); quiet(); renderer.dispose(); };
  stop.pause = () => {
    if (paused) return;
    paused = true;
    if (track && musicOn) track.pause();
    if (recorder && recorder.state === "recording") recorder.pause();
  };
  stop.resume = () => {
    if (!paused) return;
    paused = false; started = true; clock.getDelta();  // no jump for the time spent paused
    if (actx && actx.state === "suspended") actx.resume().catch(() => {});
    if (track && musicOn) track.play().catch(() => {});
    if (recorder && recorder.state === "paused") recorder.resume();
  };
  Object.defineProperty(stop, "paused", { get: () => paused });
  // step(seconds): jump the film on, for screenshots and checks (a hidden window draws almost no frames)
  stop.step = seconds => { started = true; for (let k = 0; k < seconds / 0.05; k++) tick(0.05); };
  return stop;
}

window.Film = { play, timeline };
window.dispatchEvent(new Event("film-ready"));
