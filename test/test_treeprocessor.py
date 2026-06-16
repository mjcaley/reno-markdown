from markdown import Markdown
from reno_markdown.extension import RenoReleaseNotesExtension

def test_replace_marker():
    test_input = """[release-notes]"""

    md = Markdown(extensions=[RenoReleaseNotesExtension()])
    result = md.convert(test_input)

    assert result == '<div class="reno-release-notes"></div>'
