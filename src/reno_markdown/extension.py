import xml.etree.ElementTree as etree
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generator

from markdown import Extension, Markdown
from markdown.treeprocessors import Treeprocessor

from .repository import Note, RenoRepository, Section


@dataclass
class ElementLocation:
    node: etree.Element
    parent: etree.Element
    index: int


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

    @staticmethod
    def append_note_element(parent: etree.Element, note: Note):
        note_div = etree.Element(
            "div",
            {
                "class": "reno-note",
                "data-reno-filename": note.filename,
                "data-reno-sha": note.sha.decode()
            }
        )
        note_p = etree.Element("p")
        note_p.text = f"{note.note}"
        note_div.append(note_p)
        parent.append(note_div)

    @staticmethod
    def append_section_element(parent: etree.Element, section: Section, notes: list[Note]):
        section_div = etree.Element("div", {"class": "reno-section"})
        section_h4 = etree.Element("h4")
        section_h4.text = section
        section_div.append(section_h4)
        parent.append(section_div)

        for note in notes:
            RenoReleaseNotesTreeProcessor.append_note_element(section_div, note)

    @staticmethod
    def append_version_element(parent: etree.Element, reno_repository: RenoRepository, version: str):
        version_div = etree.Element("div", {"class": "reno-version"})
        version_h3 = etree.Element("h3")
        version_h3.text = version
        version_div.append(version_h3)
        parent.append(version_div)

        for section, notes in reno_repository.sections(version):
            RenoReleaseNotesTreeProcessor.append_section_element(version_div, section, notes)

    def format_release_notes(self) -> etree.Element:
        div = etree.Element("div", {"class": "reno-release-notes"})
        h2 = etree.Element("h2")
        h2.text = self.title
        div.append(h2)

        reno_repository = RenoRepository(self.repo_root)
        for version in reno_repository.versions():
            self.append_version_element(div, reno_repository, version)

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
