from markdown import Markdown

from reno_markdown.extension import (
    RenoReleaseNotesExtension,
    RenoReleaseNotesTreeProcessor,
)


def test_replace_marker(mock_repo):
    test_input = """[release-notes]"""

    md = Markdown(
        extensions=[RenoReleaseNotesExtension(repo_root=str(mock_repo.root))],
    )
    result = md.convert(test_input)

    assert "reno-release-notes" in result
    assert "v1.0.0" in result
    assert "A mock bug fix." in result


def test_reno_loader(mock_repo):
    tree_processor = RenoReleaseNotesTreeProcessor(
        Markdown(), {"repo_root": str(mock_repo.root)}
    )
    notes = tree_processor._create_release_notes()

    assert "v1.0.0" in notes
    assert notes["v1.0.0"][0].filename == mock_repo.notes[0]
    assert notes["v1.0.0"][0].data == {"bug": ["A mock bug fix."]}
