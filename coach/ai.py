"""Optional AI explanations, using the player's own API keys (Settings: key 1, then key 2 if key 1 fails).

The AI only puts the engine's hard facts (coach.facts) into friendly words; it is told never to invent moves.
Without a key the coach uses its built-in sentences, so everything still works.
Claude goes through the official Anthropic SDK; Gemini, Groq and OpenAI through their plain web APIs.
"""
import json
import urllib.error
import urllib.request

from coach import settings
from coach.paths import DATA

CACHE = DATA / "explanations.json"
TIMEOUT = 30
AGENT = {"User-Agent": "ChessCoach (github.com/Abhra71/ChessCoach)"}  # some providers block unnamed requests (403)

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


def _post(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **AGENT, **headers})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
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


def _gemini(key, system, prompt, max_tokens):
    head = {"x-goog-api-key": key}
    if "gemini" not in _MODELS:
        listed = [m["name"].split("/", 1)[1] for m in _get("https://generativelanguage.googleapis.com/v1beta/models", head)["models"]
                  if "generateContent" in m.get("supportedGenerationMethods", [])]
        _MODELS["gemini"] = _pick(listed, ["flash-latest", "3.5-flash", "3-flash", "2.5-flash", "flash"],
                                  avoid=("lite", "image", "tts", "live", "audio", "embedding", "thinking"))
    body = {"systemInstruction": {"parts": [{"text": system}]}, "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.4}}
    out = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{_MODELS['gemini']}:generateContent", body, head)
    return "".join(p.get("text", "") for p in out["candidates"][0]["content"]["parts"]).strip()


def _openai_style(name, base, key, system, prompt, max_tokens, prefer):
    head = {"Authorization": f"Bearer {key}"}
    if name not in _MODELS:
        listed = sorted(m["id"] for m in _get(f"{base}/models", head)["data"])
        _MODELS[name] = _pick(listed, prefer, avoid=("whisper", "tts", "embed", "guard", "image", "audio", "realtime", "dall"))
    body = {"model": _MODELS[name], "max_completion_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]}
    out = _post(f"{base}/chat/completions", body, head)
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


def _call(provider, key, system, prompt, max_tokens):
    if provider == "gemini":
        return _gemini(key, system, prompt, max_tokens)
    if provider == "groq":
        return _openai_style("groq", "https://api.groq.com/openai/v1", key, system, prompt, max_tokens,
                             ["gpt-oss-120b", "llama-3.3-70b", "gpt-oss-20b"])
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
