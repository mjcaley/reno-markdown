from markdown import Markdown
from reno_markdown.extension import RenoReleaseNotesExtension, RenoReleaseNotesTreeProcessor


def test_replace_marker():
    test_input = """[release-notes]"""

    md = Markdown(extensions=[RenoReleaseNotesExtension()])
    result = md.convert(test_input)

    assert result == '''<div class="reno-release-notes">
<p text="Release notes will be generated here."></p>
</div>'''
