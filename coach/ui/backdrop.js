// The welcome screen's background: Poly Haven's antique "Chess Set" (CC0) replaying the Opera Game, slowly, in 3D.
// Offline: Three.js and the model are stored in /ui/vendor (python -m coach.get_assets).
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { BokehPass } from "three/addons/postprocessing/BokehPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
import { OPERA_GAME } from "/ui/opera_game.js";

const SQUARE = 0.058, EDGE = -0.203;  // the model's board: a1 at (-0.203, -0.203), 5.8 cm squares
const FILES = "abcdefgh";
const at = sq => new THREE.Vector3(EDGE + FILES.indexOf(sq[0]) * SQUARE, 0.017, EDGE + (Number(sq[1]) - 1) * SQUARE);

function mount(el) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "low-power" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.78;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  el.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x050505);
  scene.fog = new THREE.Fog(0x050505, 0.55, 1.4);
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.35;

  const camera = new THREE.PerspectiveCamera(32, 1, 0.01, 10);
  // depth of field: whatever the camera looks at is sharp, the rest of the board softly out of focus
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  const bokeh = new BokehPass(scene, camera, { focus: 0.5, aperture: 0.035, maxblur: 0.012 });
  composer.addPass(bokeh);
  composer.addPass(new OutputPass());
  const key = new THREE.SpotLight(0xfff1dc, 9, 2.5, Math.PI / 7, 0.55, 1.6);
  key.position.set(0.35, 0.75, 0.25);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.bias = -0.0004;
  scene.add(key, key.target);
  const rim = new THREE.DirectionalLight(0x9fb4ff, 0.6);
  rim.position.set(-0.6, 0.4, -0.5);
  scene.add(rim);

  const pieces = {};  // square -> object
  let start = {}, ready = false, step = 0, moving = null, wait = 2.5;
  new GLTFLoader().load("/ui/vendor/chess_set/chess_set_2k.gltf", gltf => {
    gltf.scene.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    scene.add(gltf.scene);
    for (const o of gltf.scene.children) {
      if (!o.name.startsWith("piece_")) continue;
      const f = Math.round((o.position.x - EDGE) / SQUARE), r = Math.round((o.position.z - EDGE) / SQUARE);
      const sq = FILES[f] + (r + 1);
      pieces[sq] = o; start[sq] = o;
    }
    ready = true;
    el.classList.add("ready");
  });

  function reset() {
    for (const o of Object.values(start)) { o.visible = true; o.scale.setScalar(1); }
    Object.keys(pieces).forEach(k => delete pieces[k]);
    for (const [sq, o] of Object.entries(start)) { pieces[sq] = o; o.position.copy(at(sq)); }
    step = 0;
  }

  function begin(s) {  // start animating one move of the game
    const piece = pieces[s.from];
    if (!piece) return;
    const jobs = [{ obj: piece, from: at(s.from), to: at(s.to), lift: piece.name.includes("knight") ? 0.085 : 0.045 }];
    if (s.rook) jobs.push({ obj: pieces[s.rook[0]], from: at(s.rook[0]), to: at(s.rook[1]), lift: 0.03 });
    const taken = s.capture ? pieces[s.capture] : null;
    delete pieces[s.from];
    if (s.capture) delete pieces[s.capture];
    pieces[s.to] = piece;
    if (s.rook) { pieces[s.rook[1]] = pieces[s.rook[0]]; delete pieces[s.rook[0]]; }
    moving = { jobs, taken, t: 0, length: 1.3 };
    focus.copy(at(s.to));
  }

  // A short film on a loop: high above, glide down beside the pieces, follow the moves, slow orbit, back up.
  const SHOTS = [
    { len: 8, at: t => new THREE.Vector3(0.05 * Math.sin(t * 0.2), 1.2, 0.14), look: () => new THREE.Vector3(0, 0, 0) },
    { len: 10, at: t => new THREE.Vector3(0.42 - t * 0.015, 0.16 - t * 0.008, 0.36 - t * 0.012), look: () => new THREE.Vector3(0, 0.03, 0) },
    { len: 14, at: t => focus.clone().add(new THREE.Vector3(0.27 * Math.cos(0.4 + t * 0.04), 0.1, 0.27 * Math.sin(0.4 + t * 0.04))),
      look: () => focus.clone().setY(0.035) },
    { len: 14, at: t => new THREE.Vector3(Math.sin(t * 0.06) * 0.6, 0.3, Math.cos(t * 0.06) * 0.6), look: () => new THREE.Vector3(0, 0.02, 0) },
  ];
  const focus = new THREE.Vector3(0, 0, 0), eye = new THREE.Vector3(0, 1.2, 0.14), aim = new THREE.Vector3();
  // ?shot=N starts the film on shot N (for Store screenshots and the trailer)
  let shot = Math.min(SHOTS.length - 1, Math.max(0, Number(new URLSearchParams(location.search).get("shot")) || 0)), shotT = 0;
  if (shot) { eye.copy(SHOTS[shot].at(0)); aim.copy(SHOTS[shot].look()); }
  const clock = new THREE.Clock();
  let alive = true;
  function frame() {
    if (!alive) return;
    requestAnimationFrame(frame);
    const dt = Math.min(clock.getDelta(), 0.05);
    if ((shotT += dt) > SHOTS[shot].len) { shot = (shot + 1) % SHOTS.length; shotT = 0; }
    const ease = 1 - Math.exp(-dt * 0.9);  // glide between shots instead of cutting
    eye.lerp(SHOTS[shot].at(shotT), ease);
    aim.lerp(SHOTS[shot].look(), ease * 1.4);
    camera.position.copy(eye);
    camera.lookAt(aim);
    bokeh.uniforms.focus.value = eye.distanceTo(aim);
    bokeh.uniforms.aperture.value = shot === 0 ? 0.004 : 0.035;  // from high above, everything is sharp
    if (ready) {
      if (moving) {
        moving.t += dt;
        const k = Math.min(1, moving.t / moving.length), e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
        for (const j of moving.jobs) {
          j.obj.position.lerpVectors(j.from, j.to, e);
          j.obj.position.y = 0.017 + Math.sin(Math.PI * e) * j.lift + (k > 0.92 ? Math.sin((k - 0.92) / 0.08 * Math.PI) * -0.0015 : 0);
        }
        if (moving.taken) { moving.taken.scale.setScalar(Math.max(0.001, 1 - e)); if (k >= 1) moving.taken.visible = false; }
        if (k >= 1) { moving = null; wait = step >= OPERA_GAME.length ? 6 : 1.6; }
      } else if ((wait -= dt) <= 0) {
        if (step >= OPERA_GAME.length) reset();
        else begin(OPERA_GAME[step++]);
        wait = 1.6;
      }
    }
    composer.render(dt);
  }

  function size() {
    const w = el.clientWidth || window.innerWidth, h = el.clientHeight || window.innerHeight;
    renderer.setSize(w, h, false);
    composer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  window.addEventListener("resize", size);
  size();
  frame();
  return () => { alive = false; composer.dispose(); renderer.dispose(); window.removeEventListener("resize", size); };
}

window.Backdrop = { mount };
window.dispatchEvent(new Event("backdrop-ready"));
