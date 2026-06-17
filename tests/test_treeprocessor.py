from markdown import Markdown
from reno_markdown.extension import (
    RenoReleaseNotesExtension,
    RenoReleaseNotesTreeProcessor,
)


def test_replace_marker(mock_repo):
    test_input = """[release-notes]"""

    md = Markdown(
        extensions=[RenoReleaseNotesExtension()],
        extension_configs={
            "RenoReleaseNotesExtension": {"repo_root": str(mock_repo.root)}
        },
    )
    result = md.convert(test_input)

    assert (
        result
        == """<div class="reno-release-notes">
<p>Release notes will be generated here.</p>
</div>"""
    )


def test_reno_loader(mock_repo):
    tree_processor = RenoReleaseNotesTreeProcessor(
        None, {"repo_root": str(mock_repo.root)}
    )
    notes = [note for note in tree_processor.get_release_notes()]

    assert notes[0].version == "v1.0.0"
    assert notes[0].filename == str(mock_repo.notes[0])
    assert notes[0].data == {"bug": ["A mock bug fix."]}
