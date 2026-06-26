from markdown import Markdown

from reno_markdown.extension import (
    RenoReleaseNotesExtension,
    RenoReleaseNotesBlockProcessor,
)


def test_replace_marker(mock_repo):
    test_input = """:::reno-release-notes\n:::\n"""

    md = Markdown(
        extensions=[RenoReleaseNotesExtension(repo_root=str(mock_repo.root))],
    )
    result = md.convert(test_input)

    assert "reno-release-notes" in result
    assert "v1.0.0" in result
    assert "A mock bug fix." in result
