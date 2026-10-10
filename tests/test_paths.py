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
