from dataclasses import dataclass
from pathlib import Path
import typing
import xml.etree.ElementTree as etree
from markdown import Extension
from markdown.treeprocessors import Treeprocessor
from reno.config import Config
from reno.loader import Loader

if typing.TYPE_CHECKING:
    from markdown import Markdown
    from typing import Any, Generator


@dataclass
class ElementLocation:
    node: etree.Element
    parent: etree.Element
    index: int


@dataclass
class ReleaseNote:
    version: str
    filename: Path
    sha: str
    data: dict[str, Any]


def iter_parent_child(root: etree.Element) -> Generator[ElementLocation, None, None]:
    for index, child in enumerate(root):
        yield from iter_parent_child(child)
        yield ElementLocation(node=child, parent=root, index=index)


class RenoReleaseNotesTreeProcessor(Treeprocessor):
    def __init__(self, md: Markdown, config: dict[str, Any]):
        super().__init__(md)

        self.title: str = config.get("title", "Release Notes")
        self.repo_root = Path(config["repo_root"])

    def get_release_notes(self) -> Generator[ReleaseNote, None, None]:
        config = Config(str(self.repo_root))
        with Loader(config) as loader:
            for version in loader.versions:
                for filename, sha in loader[version]:
                    yield ReleaseNote(
                        version=version,
                        filename=filename,
                        sha=sha,
                        data=loader.parse_note_file(filename, sha),
                    )

    def build_release_notes_element(self) -> etree.Element:
        div = etree.Element("div", {"class": "reno-release-notes"})
        p = etree.Element("p")
        p.text = "Release notes will be generated here."
        div.append(p)

        return div

    def run(self, root: etree.Element):
        for element in iter_parent_child(root):
            if element.node.text and element.node.text.strip() == "[release-notes]":
                reno_element = self.build_release_notes_element()

                element.parent.remove(element.node)
                element.parent.insert(element.index, reno_element)

        return None


class RenoReleaseNotesExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {
            "repo_root": [None, "Path to the root of the repository"],
            "title": ["Release Notes", "Title for the release notes section"],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md: Markdown):
        md.treeprocessors.register(
            RenoReleaseNotesTreeProcessor(md, self.getConfigs()),
            "reno_release_notes",
            15,
        )
