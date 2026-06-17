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
        repo_root = config.get("repo_root") or "."
        self.repo_root = Path(repo_root)

    def _get_notes(self, loader: Loader, version: str) -> Generator[ReleaseNote, None, None]:
        for filename, sha in loader[version]:
            yield ReleaseNote(
                version=version,
                filename=Path(filename),
                sha=sha,
                data=loader.parse_note_file(filename, sha),
            )

    def _get_versions(self, loader: Loader) -> Generator[str, None, None]:
        for version in loader.versions:
            yield version

    def _create_release_notes(self) -> dict[str, list[ReleaseNote]]:
        release_notes = {}
        with Loader(Config(str(self.repo_root))) as loader:
            for version in self._get_versions(loader):
                release_notes[version] = list(self._get_notes(loader, version))

        return release_notes

    def format_release_notes(self) -> etree.Element:
        notes = self._create_release_notes()
        self.md.reno_release_notes = notes

        div = etree.Element("div", {"class": "reno-release-notes"})
        h2 = etree.Element("h2")
        h2.text = self.title
        div.append(h2)

        for version in notes.keys():
            version_div = etree.Element("div", {"class": "reno-version"})
            version_h3 = etree.Element("h3")
            version_h3.text = version
            version_div.append(version_h3)

            for note in notes[version]:
                note_div = etree.Element("div", {"class": "reno-note"})
                note_p = etree.Element("p")
                note_p.text = f"{note.data.get('bug', [''])[0]}"
                note_div.append(note_p)
                version_div.append(note_div)

            div.append(version_div)

        return div

    def build_release_notes_element(self) -> etree.Element:
        div = etree.Element("div", {"class": "reno-release-notes"})
        notes = self.format_release_notes()
        div.append(notes)

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
            "repo_root": [".", "Path to the root of the repository"],
            "title": ["Release Notes", "Title for the release notes section"],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md: Markdown):
        md.treeprocessors.register(
            RenoReleaseNotesTreeProcessor(md, self.getConfigs()),
            "reno_release_notes",
            15,
        )
