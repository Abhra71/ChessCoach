"""The player's settings: theme, voice, and two optional AI key slots.

Plain settings live in data/settings.json. API keys are never written there: they go to Windows Credential Manager
(through keyring), encrypted for this Windows user, and the app only ever shows the last 4 characters.
"""
import json

import keyring

from coach.paths import DATA

FILE = DATA / "settings.json"
VAULT = "ChessCoach"  # the name the keys are stored under in Windows Credential Manager
SLOTS = ("slot1", "slot2")
PROVIDERS = {  # what the player can choose for a slot; "free" means the provider has a free tier
    "gemini": {"name": "Google Gemini", "free": True, "get_key": "https://aistudio.google.com/apikey"},
    "groq": {"name": "Groq", "free": True, "get_key": "https://console.groq.com/keys"},
    "anthropic": {"name": "Anthropic Claude", "free": False, "get_key": "https://console.anthropic.com/settings/keys"},
    "openai": {"name": "OpenAI", "free": False, "get_key": "https://platform.openai.com/api-keys"},
}
DEFAULTS = {"theme": "system", "voice": True, "voice_name": "af_heart",
            "slot1": {"provider": "gemini"}, "slot2": {"provider": "groq"}}


def load():
    stored = json.loads(FILE.read_text()) if FILE.exists() else {}
    return {**DEFAULTS, **stored}


def save(changes):
    """Merge allowed changes into the settings file. Returns the new settings."""
    current = load()
    if changes.get("theme") in ("system", "dark", "light"):
        current["theme"] = changes["theme"]
    if isinstance(changes.get("voice"), bool):
        current["voice"] = changes["voice"]
    from coach.voice import CHOICES
    if changes.get("voice_name") in CHOICES:
        current["voice_name"] = changes["voice_name"]
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps({k: v for k, v in current.items() if k in DEFAULTS}, indent=2))
    return current


def set_key(slot, provider, key):
    if slot not in SLOTS or provider not in PROVIDERS:
        raise ValueError("unknown slot or provider")
    key = key.strip()
    if not 16 <= len(key) <= 300 or any(c.isspace() for c in key):
        raise ValueError("That doesn't look like an API key.")
    keyring.set_password(VAULT, slot, key)
    current = load()
    current[slot] = {"provider": provider}
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps({k: v for k, v in current.items() if k in DEFAULTS}, indent=2))


def remove_key(slot):
    if slot not in SLOTS:
        raise ValueError("unknown slot")
    try:
        keyring.delete_password(VAULT, slot)
    except keyring.errors.PasswordDeleteError:
        pass


def get_key(slot):
    """The key itself, for the AI client only. Never send it to the pages."""
    return keyring.get_password(VAULT, slot)


def public():
    """Settings as the app pages may see them: keys only as 'set, ends with …abcd'."""
    s = load()
    slots = {}
    for slot in SLOTS:
        key = get_key(slot)
        slots[slot] = {"provider": s[slot]["provider"], "set": bool(key), "ends": key[-4:] if key else None}
    from coach import voice
    return {"theme": s["theme"], "voice": s["voice"], "voice_name": s["voice_name"], "voices": voice.CHOICES,
            "voice_ready": voice.available(), "slots": slots, "providers": PROVIDERS}
