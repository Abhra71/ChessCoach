"""Optional AI explanations, using the player's own API keys (Settings: key 1, then key 2 if key 1 fails).

The AI only puts the engine's hard facts (coach.facts) into friendly words; it is told never to invent moves.
Without a key the coach uses its built-in sentences, so everything still works.
Claude goes through the official Anthropic SDK; Gemini, Groq and OpenAI through their plain web APIs.
"""
import json
import time
import urllib.error
import urllib.request
from datetime import date

from coach import settings
from coach.paths import DATA

CACHE = DATA / "explanations.json"
USAGE = DATA / "ai-usage.json"
REST_MINUTES = 10  # a provider that says it's busy gets this long to rest before we ask it again
# the smaller model, used when the main one is busy: picked from the provider's own list, like the main one, because
# fixed names get retired (20 Oct 2026: Groq's llama-3.1-8b-instant and llama-3.3-70b were gone, and every fallback
# answered 404)
SMALL = {"groq": ["gpt-oss-20b", "qwen3", "llama"], "gemini": ["flash-lite-latest", "flash-lite"]}
THINK_ROOM = 1024  # reasoning models think before answering, and that counts against the length: room for it
_REST = {}  # provider -> time it may be asked again
_LAST = {}  # provider -> the rate-limit headers of its last answer
TIMEOUT = 20  # a spoken reply that takes longer is no use: the next key, or the written sentences
AGENT = {"User-Agent": "Knightwise (github.com/Abhra71/ChessCoach)"}  # some providers block unnamed requests (403)

COACH_RULES = (
    "You are a warm, clear chess coach for a beginner (chess.com rating about {rating}). "
    "Speak to the player as 'you'. Use plain words; name squares and pieces like 'your bishop on d3'. "
    "Use ONLY the facts given to you, which come from the Stockfish engine and the board: never invent a move, "
    "a threat or a tactic that is not in the facts. If the facts don't show why, say what the engine's line shows. "
    "In the engine's line, 'You play' moves are the player's and 'They play' moves are the opponent's. "
    "No headings, no lists, no chess jargon like 'tempo' or 'zwischenzug'. "
)


class NoKey(Exception):
    pass


def _post(url, body, headers, provider=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **AGENT, **headers})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        if provider:  # Groq tells us exactly how much is left: kept for the usage panel
            limits = {k.lower(): v for k, v in resp.headers.items() if k.lower().startswith("x-ratelimit-")}
            if limits:
                _LAST[provider] = limits
        return json.load(resp)


def _get(url, headers):
    with urllib.request.urlopen(urllib.request.Request(url, headers={**AGENT, **headers}), timeout=TIMEOUT) as resp:
        return json.load(resp)


def _pick(names, prefer, avoid=()):
    names = [n for n in names if not any(a in n for a in avoid)]
    for p in prefer:
        for n in names:
            if p in n:
                return n
    return names[0] if names else None


_MODELS = {}  # provider -> model chosen from the provider's own list (once per run)
_LISTED = {}  # provider -> its list of models, for choosing the smaller one too


def _gemini(key, system, prompt, max_tokens, model=None):
    head = {"x-goog-api-key": key}
    if "gemini" not in _MODELS:
        listed = [m["name"].split("/", 1)[1] for m in _get("https://generativelanguage.googleapis.com/v1beta/models", head)["models"]
                  if "generateContent" in m.get("supportedGenerationMethods", [])]
        _LISTED["gemini"] = listed
        # Google's own pointer to its current Flash-Lite model, so retired versions never stick. Lite, not Flash: on
        # 20 Oct the full Flash took over 30 seconds or timed out, Lite answered in 1.6 s, and a coach's spoken reply
        # is three short sentences
        _MODELS["gemini"] = _pick(listed, ["flash-lite-latest", "flash-latest", "flash-lite", "flash"],
                                  avoid=("image", "tts", "live", "audio", "embedding", "thinking", "preview"))
    body = {"systemInstruction": {"parts": [{"text": system}]}, "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens + THINK_ROOM, "temperature": 0.4}}
    out = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{model or _MODELS['gemini']}:generateContent",
                body, head, "gemini")
    _count("gemini", (out.get("usageMetadata") or {}).get("totalTokenCount", 0))
    return "".join(p.get("text", "") for p in out["candidates"][0]["content"]["parts"]).strip()


AVOID = ("whisper", "tts", "embed", "guard", "image", "audio", "realtime", "dall", "orpheus", "allam")


def _openai_style(name, base, key, system, prompt, max_tokens, prefer, model=None):
    head = {"Authorization": f"Bearer {key}"}
    if name not in _MODELS:
        _LISTED[name] = sorted(m["id"] for m in _get(f"{base}/models", head)["data"])
        _MODELS[name] = _pick(_LISTED[name], prefer, avoid=AVOID)
    use = model or _MODELS[name]
    body = {"model": use, "max_completion_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]}
    if "gpt-oss" in use:  # it thinks first: briefly, with room for it, or the answer came back cut off or empty (20 Oct)
        body.update(reasoning_effort="low", max_completion_tokens=max_tokens + THINK_ROOM)
    out = _post(f"{base}/chat/completions", body, head, name)
    _count(name, (out.get("usage") or {}).get("total_tokens", 0))
    return out["choices"][0]["message"]["content"].strip()


def _claude(key, system, prompt, max_tokens):
    import anthropic
    client = anthropic.Anthropic(api_key=key, timeout=TIMEOUT)
    response = client.beta.messages.create(
        model="claude-opus-5-5",
        max_tokens=max_tokens,
        system=system,
        output_config={"effort": "low"},  # short explanations: low effort is enough and keeps the player's cost down
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",  # if the request is declined, the API retries it on a suitable model
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude declined to answer.")
    return "".join(b.text for b in response.content if b.type == "text").strip()


BUSY = (429, 500, 502, 503, 504)  # out of quota for now, or overloaded: the provider needs a rest


def _busy(e):
    if isinstance(e, urllib.error.HTTPError):
        return e.code in BUSY
    return "overloaded" in str(e).lower() or "timed out" in str(e).lower()


def resting(provider, now=None):
    return _REST.get(provider, 0) > (now or time.time())


def _rest(provider):
    _REST[provider] = time.time() + REST_MINUTES * 60


def _call(provider, key, system, prompt, max_tokens):
    """One request: the main model; if it's busy, the provider's smaller model; if that's busy too, the provider
    rests for REST_MINUTES and the next key is tried. A retired model (404/410) is picked again from the list once."""
    try:
        return _call_once(provider, key, system, prompt, max_tokens)
    except Exception as e:
        if isinstance(e, urllib.error.HTTPError) and e.code in (404, 410) and provider in _MODELS:
            _MODELS.pop(provider)
            return _call_once(provider, key, system, prompt, max_tokens)
        if not _busy(e):
            raise
        if provider not in SMALL:
            _rest(provider)
            raise
    small = _pick(_LISTED.get(provider, []), SMALL[provider], avoid=AVOID + (_MODELS.get(provider) or "~",))
    if not small:
        _rest(provider)
        raise
    try:
        return _call_once(provider, key, system, prompt, max_tokens, model=small)
    except Exception as e:
        if _busy(e):
            _rest(provider)
        raise


def _call_once(provider, key, system, prompt, max_tokens, model=None):
    if provider == "gemini":
        return _gemini(key, system, prompt, max_tokens, model)
    if provider == "groq":
        return _openai_style("groq", "https://api.groq.com/openai/v1", key, system, prompt, max_tokens,
                             ["gpt-oss-120b", "llama-3.3-70b", "gpt-oss-20b"], model)
    if provider == "openai":
        return _openai_style("openai", "https://api.openai.com/v1", key, system, prompt, max_tokens,
                             ["gpt-5-mini", "gpt-5.1-mini", "gpt-4.1-mini", "gpt-4o-mini"])
    if provider == "anthropic":
        return _claude(key, system, prompt, max_tokens)
    raise ValueError(f"unknown provider {provider}")


def ready():
    return any(settings.get_key(slot) for slot in settings.SLOTS)


def complete(system, prompt, max_tokens=700):
    """Ask key 1, then key 2. Returns (text, provider). Raises NoKey when no key is set."""
    s, errors = settings.load(), []
    for slot in settings.SLOTS:
        key = settings.get_key(slot)
        if not key:
            continue
        provider = s[slot]["provider"]
        if resting(provider):  # it said it was busy a few minutes ago: don't make the player wait on it again
            errors.append(f"{provider}: resting")
            continue
        try:
            text = _call(provider, key, system, prompt, max_tokens)
            if text:
                return text, provider
            errors.append(f"{provider}: empty answer")
        except urllib.error.HTTPError as e:
            errors.append(f"{provider}: HTTP {e.code}")
        except Exception as e:  # network, quota, model gone: try the next key
            errors.append(f"{provider}: {str(e)[:120]}")
    if not errors:
        raise NoKey("No AI key set. Add one in Settings.")
    raise RuntimeError("; ".join(errors))


def _usage():
    try:
        return json.loads(USAGE.read_text())
    except (OSError, ValueError):
        return {}


def _count(provider, tokens, today=None):
    """Requests and tokens used today, per provider; a week is kept."""
    day = (today or date.today()).isoformat()
    u = _usage()
    d = u.setdefault(day, {}).setdefault(provider, {"requests": 0, "tokens": 0})
    d["requests"] += 1
    d["tokens"] += int(tokens or 0)
    for old in sorted(u)[:-7]:
        u.pop(old)
    USAGE.parent.mkdir(parents=True, exist_ok=True)
    USAGE.write_text(json.dumps(u))


def usage(now=None):
    """For the usage panel: today's use per provider, what the provider says is left (Groq says it exactly),
    and how long a busy provider is still resting."""
    now = now or time.time()
    today = _usage().get(date.today().isoformat(), {})
    out = {}
    for provider in settings.PROVIDERS:
        used, last = today.get(provider, {"requests": 0, "tokens": 0}), _LAST.get(provider, {})

        def num(k):
            return int(last[k]) if str(last.get(k, "")).isdigit() else None
        out[provider] = {**used, "requests_left": num("x-ratelimit-remaining-requests"),
                         "requests_limit": num("x-ratelimit-limit-requests"),
                         "tokens_left": num("x-ratelimit-remaining-tokens"), "tokens_limit": num("x-ratelimit-limit-tokens"),
                         "resets": last.get("x-ratelimit-reset-requests"),
                         "resting_minutes": max(1, round((_REST[provider] - now) / 60)) if resting(provider, now) else 0}
    return out


def test_key(slot):
    """A tiny request to check a saved key works. Returns (ok, message)."""
    key, provider = settings.get_key(slot), settings.load()[slot]["provider"]
    if not key:
        return False, "No key saved in this slot."
    try:
        _call(provider, key, "Reply with one word.", "Say: ready", 300)
        return True, f"Works ({settings.PROVIDERS[provider]['name']}{', ' + _MODELS[provider] if provider in _MODELS else ''})."
    except urllib.error.HTTPError as e:
        return False, {400: "The provider refused the request (bad key?).", 401: "The key was refused.",
                       403: "The key isn't allowed to do this.", 429: "Out of free quota for now."}.get(e.code, f"HTTP {e.code}")
    except Exception as e:
        return False, str(e)[:160]


def _cache():
    return json.loads(CACHE.read_text()) if CACHE.exists() else {}


def explain(facts, rating):
    """A coach-style explanation of one key moment, grounded in `facts`. Cached per position and move."""
    cache_key = f"{facts['fen']}|{facts['played']}"
    cache = _cache()
    if cache_key in cache:
        return cache[cache_key]
    system = COACH_RULES.format(rating=rating or "unknown") + \
        "Explain this moment in 2 or 3 short sentences: what went wrong with the move played, and why the better move is better. " \
        "End with one short habit to remember."
    prompt = "Facts about this moment (from Stockfish and the board):\n" + json.dumps({k: v for k, v in facts.items() if k != "fen"}, indent=1)
    text, provider = complete(system, prompt)
    cache[cache_key] = {"text": text, "provider": provider}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache))
    return cache[cache_key]


def ask(question, context, rating):
    """Answer the player's own question about a position, using only the engine facts in `context`."""
    system = COACH_RULES.format(rating=rating or "unknown") + \
        "Answer the player's question in at most 4 short sentences, using only the facts. " \
        "If the question can't be answered from the facts, say so kindly and suggest what to look at."
    prompt = f"Facts (from Stockfish and the board):\n{json.dumps(context, indent=1)}\n\nThe player asks: {question[:500]}"
    text, provider = complete(system, prompt)
    return {"text": text, "provider": provider}


# ---------- hearing: the player's voice -> words, through the same keys (0.6, flagship 2) ----------
# Jarvis's record (jarvis-keep logs): Groq's cloud whisper-large-v3 heard 107 sentences at about 0.5 s each with no
# failures, where Whisper on the PC misheard often. So: Groq first, Gemini as the backup, nothing on the PC by default.
HEAR_MODEL = {"groq": "whisper-large-v3"}
HEAR_HINT = ("A chess player talking to their coach Maya or Viktor. Words: knight, bishop, rook, queen, king, pawn, "
             "takes, castle, kingside, queenside, check, checkmate, mate, mate in one, fork, pin, skewer, e4, d4, Nf3, Bc4, Caro-Kann, "
             "Sicilian, Italian Game, rematch it, review, next, go back, stop talking, practice, puzzle, opening, endgame.")


_HINT = {"at": 0.0, "text": HEAR_HINT}


def hear_hint():
    """The hint plus the names the player is likely to say: their recent opponents (19 Oct hearing test: usernames
    were the words heard wrong most, "waiyanji" as "Wei Yanji", "lmaongabs" as "El Moungabs"). Worked out at most
    every 5 minutes: reading the games on every sentence made hearing 0.2 s slower."""
    if time.time() - _HINT["at"] > 300:
        try:
            from coach import heard, insights
            # the names the player has actually asked for first (learned), then their latest opponents
            names = list(dict.fromkeys(heard.words(6) + [g["opponent"] for g in insights.games_list()[:12]]))[:10]
        except Exception:
            names = []
        _HINT.update(at=time.time(), text=HEAR_HINT + (f" Opponents: {', '.join(names)}." if names else ""))
    return _HINT["text"]


def wav(pcm16, rate=16000):
    """16-bit mono samples -> a WAV file in memory."""
    import io
    import wave as wavefile
    buf = io.BytesIO()
    with wavefile.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm16)
    return buf.getvalue()


def _groq_hear(key, audio):
    import uuid
    boundary = uuid.uuid4().hex
    fields = {"model": HEAR_MODEL["groq"], "language": "en", "prompt": hear_hint(), "response_format": "verbose_json",
              "temperature": "0"}
    body = b"".join(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
                    for k, v in fields.items())
    body += (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="speech.wav"\r\n'
             f"Content-Type: audio/wav\r\n\r\n").encode() + audio + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request("https://api.groq.com/openai/v1/audio/transcriptions", data=body,
                                 headers={"Authorization": f"Bearer {key}", **AGENT,
                                          "Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        out = json.load(resp)
    _count("groq", 0)
    # Whisper "hears" stock lines in near silence ("Subtitles by the Amara.org community", 22 Oct test): keep only
    # the parts its own score says were speech
    segs = out.get("segments")
    if segs:
        return " ".join(x.get("text", "").strip() for x in segs if (x.get("no_speech_prob") or 0) < NO_SPEECH).strip()
    return (out.get("text") or "").strip()


def _gemini_hear(key, audio):
    import base64
    head = {"x-goog-api-key": key}
    if "gemini" not in _MODELS:
        _gemini(key, "Reply with one word.", "Say: ready", 5)  # picks the model from Google's own list
    body = {"contents": [{"role": "user", "parts": [
        {"text": "Write down exactly what is said in this recording, word for word. " + hear_hint() +
                 " Reply with the words only; if nothing is said, reply with nothing."},
        {"inline_data": {"mime_type": "audio/wav", "data": base64.b64encode(audio).decode()}}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 200}}
    out = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{_MODELS['gemini']}:generateContent",
                body, head, "gemini")
    _count("gemini", (out.get("usageMetadata") or {}).get("totalTokenCount", 0))
    parts = ((out.get("candidates") or [{}])[0].get("content") or {}).get("parts") or []
    return "".join(p.get("text", "") for p in parts).strip()


HEARERS = {"groq": _groq_hear, "gemini": _gemini_hear}


NO_SPEECH = 0.6  # Whisper's own chance that a part had no speech in it: above this, it's dropped
QUIET = 600  # the loudest moment of a recording, out of 32767: below this nobody spoke (a click, the room)


def loud_enough(pcm16):
    """Was anything said at all? The loudest sample of the recording, so near silence is never sent to be heard."""
    from array import array
    a = array("h")
    a.frombytes(pcm16[: len(pcm16) - len(pcm16) % 2])
    return bool(a) and max(abs(min(a)), max(a)) >= QUIET


def hear(pcm16, rate=16000, hearers=None):
    """The player's words, through key 1 then key 2 (only Groq and Gemini can hear). Returns (text, provider).
    Raises NoKey when no key that can hear is set."""
    hearers = hearers or HEARERS
    if not loud_enough(pcm16):
        return "", None
    audio, s, errors = wav(pcm16, rate), settings.load(), []
    for slot in settings.SLOTS:
        key, provider = settings.get_key(slot), s[slot]["provider"]
        if not key or provider not in hearers:
            continue
        if resting(provider):
            errors.append(f"{provider}: resting")
            continue
        try:
            return hearers[provider](key, audio), provider
        except Exception as e:
            if _busy(e):
                _rest(provider)
            errors.append(f"{provider}: {getattr(e, 'code', '') or str(e)[:80]}")
    if not errors:
        raise NoKey("Talking needs a free Groq or Gemini key. Add one in Settings.")
    raise RuntimeError("; ".join(errors))
