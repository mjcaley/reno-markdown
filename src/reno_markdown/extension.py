from collections import defaultdict
from dataclasses import dataclass, field
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


@dataclass
class Note:
    filename: str
    sha: str
    note: str


@dataclass
class Version:
    sections: dict[str, list[Note]] = field(default_factory=lambda: defaultdict(list))


@dataclass
class ReleaseNotes:
    versions: dict[str, Version] = field(default_factory=lambda: defaultdict(Version))


class NotesBuilder:
    def __init__(self):
        self.release_notes = ReleaseNotes()

    def add(self, version: str, note: ReleaseNote):
        for section, notes in note.data.items():
            self.release_notes.versions[version].sections[section].append(Note(
                filename=note.filename, sha=note.sha, note=notes))


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

    def _create_release_notes(self) -> ReleaseNotes:
        release_notes = ReleaseNotes()
        with Loader(Config(str(self.repo_root))) as loader:
            for version in self._get_versions(loader):
                for note_file in self._get_notes(loader, version):
                    for section, note in note_file.data.items():
                        release_notes.versions[version].sections[section].append(Note(
                            filename=note_file.filename, sha=note_file.sha, note=note))

        return release_notes

    def format_release_notes(self) -> etree.Element:
        release_notes = self._create_release_notes()
        self.md.reno_release_notes = release_notes

        div = etree.Element("div", {"class": "reno-release-notes"})
        h2 = etree.Element("h2")
        h2.text = self.title
        div.append(h2)

        for version, sections in release_notes.versions.items():
            version_div = etree.Element("div", {"class": "reno-version"})
            version_h3 = etree.Element("h3")
            version_h3.text = version
            version_div.append(version_h3)

            for section, notes in sections.sections.items():
                section_div = etree.Element("div", {"class": "reno-section"})
                section_h4 = etree.Element("h4")
                section_h4.text = section
                section_div.append(section_h4)
                version_div.append(section_div)

                for note in notes:
                    note_div = etree.Element("div", {"class": "reno-note"})
                    note_p = etree.Element("p")
                    note_p.text = f"{note.note}"
                    note_div.append(note_p)
                    section_div.append(note_div)

            div.append(version_div)

        return div

    def build_release_notes_element(self) -> etree.Element:
        div = etree.Element("div", {"class": "reno-release-notes"})
        notes = self.format_release_notes()
        div.append(notes)

        return div

    def run(self, root: etree.Element) -> None:
        for element in iter_parent_child(root):
            if element.node.text and element.node.text.strip() == "[reno-release-notes]":
                reno_element = self.build_release_notes_element()

                element.parent.remove(element.node)
                element.parent.insert(element.index, reno_element)


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
