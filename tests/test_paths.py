from coach import paths


def test_source_run_is_not_the_store_app():
    assert paths.PACKAGE is None and not paths.PACKAGED
    assert paths.EXTENSION == paths.PROJECT / "extension"
    paths.place_extension()  # does nothing outside the Store app


def test_documents_folder_exists():
    assert paths.documents().is_dir()


def test_store_manifest_matches_partner_center():
    text = (paths.PROJECT / "installer" / "msix" / "AppxManifest.xml").read_text(encoding="utf-8")
    assert 'Name="Abhra71.Knightwise"' in text
    assert 'Publisher="CN=D43461BE-8C8C-4E7A-A1D9-5573364016D1"' in text
    assert "<PublisherDisplayName>Abhra71</PublisherDisplayName>" in text


def test_store_app_copies_the_extension(tmp_path, monkeypatch):
    target = tmp_path / "Knightwise" / "extension"
    monkeypatch.setattr(paths, "PACKAGED", True)
    monkeypatch.setattr(paths, "EXTENSION", target)
    paths.place_extension()
    assert (target / "manifest.json").exists() and (target / "coach.js").exists()
    (target / "coach.js").write_text("old", encoding="utf-8")
    paths.place_extension()  # same version: left alone
    assert (target / "coach.js").read_text(encoding="utf-8") == "old"


def test_first_start_always_shows_the_window(monkeypatch):
    from coach import app
    monkeypatch.setattr(app.sys, "argv", ["Knightwise.exe", "--background"])
    assert app.at_login(set_up=False) is False
    assert app.at_login(set_up=True) is True


def test_store_app_keeps_its_own_data_apart_from_the_old_chess_coach(monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(paths.PROJECT / "Local"))
    store = paths.home_for("Abhra71.Knightwise_2zqxgm1k7h82j", frozen=True)
    assert store.parts[-3:] == ("Packages", "Abhra71.Knightwise_2zqxgm1k7h82j", "LocalState")
    assert paths.home_for(None, frozen=True).name == "ChessCoach"
    assert paths.home_for(None, frozen=False) == paths.PROJECT


def test_try_fresh_uses_its_own_folder(monkeypatch, tmp_path):
    monkeypatch.setenv("KNIGHTWISE_HOME", str(tmp_path))
    assert paths.home_for("Abhra71.Knightwise_x", frozen=True) == tmp_path
    assert paths.home_for(None, frozen=False) == tmp_path
