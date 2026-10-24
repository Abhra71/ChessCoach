import pytest

from coach import settings


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    vault = {}
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    monkeypatch.setattr(settings.keyring, "set_password", lambda s, u, p: vault.__setitem__((s, u), p))
    monkeypatch.setattr(settings.keyring, "get_password", lambda s, u: vault.get((s, u)))
    def delete(s, u):  # like Windows Credential Manager: deleting a missing key is an error
        if (s, u) not in vault:
            raise settings.keyring.errors.PasswordDeleteError(u)
        del vault[(s, u)]
    monkeypatch.setattr(settings.keyring, "delete_password", delete)
    return vault


def test_defaults_and_theme():
    assert settings.load()["theme"] == "system"
    assert settings.save({"theme": "dark", "voice": False, "evil": 1})["theme"] == "dark"
    assert "evil" not in settings.load()


def test_key_goes_to_vault_not_file(isolated):
    settings.set_key("slot1", "gemini", "AIzaSyTESTKEY1234567890abcd")
    assert "AIzaSy" not in settings.FILE.read_text()
    assert isolated[("Knightwise", "slot1")] == "AIzaSyTESTKEY1234567890abcd"
    pub = settings.public()["slots"]["slot1"]
    assert pub == {"provider": "gemini", "set": True, "ends": "abcd"}


def test_bad_key_refused_and_remove():
    with pytest.raises(ValueError):
        settings.set_key("slot2", "groq", "short")
    with pytest.raises(ValueError):
        settings.set_key("slot3", "groq", "x" * 40)
    settings.set_key("slot2", "groq", "gsk_" + "x" * 40)
    settings.remove_key("slot2")
    assert settings.public()["slots"]["slot2"]["set"] is False


def test_a_key_saved_under_the_old_name_is_moved_over(isolated):
    isolated[("ChessCoach", "slot1")] = "gsk_" + "y" * 40  # saved by Chess Coach, before the rename
    assert settings.get_key("slot1") == "gsk_" + "y" * 40
    assert isolated[("Knightwise", "slot1")] == "gsk_" + "y" * 40 and ("ChessCoach", "slot1") not in isolated


def test_a_test_copy_has_keys_of_its_own(monkeypatch):
    """try test: KNIGHTWISE_VAULT gives the copy its own keys, and never moves the player's old ones into it."""
    import importlib
    from coach import settings
    monkeypatch.setenv("KNIGHTWISE_VAULT", "Knightwise-test")
    fresh = importlib.reload(settings)
    try:
        assert fresh.VAULT == "Knightwise-test" and fresh.OLD_VAULT is None
    finally:
        monkeypatch.delenv("KNIGHTWISE_VAULT")
        importlib.reload(settings)


def test_the_key_says_whose_it_is():
    from coach import settings
    assert settings.provider_of("gsk_abcdefghijklmnop") == "groq"
    assert settings.provider_of("AIzaSyabcdefghijklmnop") == "gemini"
    assert settings.provider_of("sk-ant-abcdefghijklmnop") == "anthropic"
    assert settings.provider_of("sk-proj-abcdefghijklmnop") == "openai"
    assert settings.provider_of("something-else-entirely") is None


def test_the_same_key_twice_is_refused(monkeypatch):
    import pytest
    from coach import settings
    saved = {"slot1": "gsk_abcdefghijklmnopqrst"}
    monkeypatch.setattr(settings, "get_key", lambda slot: saved.get(slot))
    with pytest.raises(ValueError, match="already saved as AI key 1"):
        settings.set_key("slot2", "gemini", "gsk_abcdefghijklmnopqrst")
