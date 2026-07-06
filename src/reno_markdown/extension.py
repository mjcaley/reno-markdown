import xml.etree.ElementTree as etree
from pathlib import Path
from typing import Any

from markdown import Extension, Markdown
from markdown.blockparser import BlockParser
from markdown.blockprocessors import BlockProcessor

from .repository import Note, RenoSection, RenoVersion, open_reno_repository


class RenoReleaseNotesBlockProcessor(BlockProcessor):
    def __init__(self, md: BlockParser, config: dict[str, Any]):
        super().__init__(md)

        self.title: str = config.get("title", "Release Notes")
        repo_root = config.get("repo_root") or "."
        self.repo_root = Path(repo_root)
        self.release_notes_dir: str | None = config.get("release_notes_dir")

    @staticmethod
    def append_note_element(parent: etree.Element, note: Note):
        note_p = etree.Element(
            "p",
            {
                "class": "reno-note",
                "data-reno-filename": note.filename,
                "data-reno-sha": note.sha,
            },
        )
        note_p.text = note.note
        parent.append(note_p)

    @staticmethod
    def append_prelude_element(parent: etree.Element, notes: list[Note]):
        prelude_div = etree.Element("div", {"class": "reno-prelude"})
        parent.append(prelude_div)

        for note in notes:
            RenoReleaseNotesBlockProcessor.append_note_element(prelude_div, note)

    @staticmethod
    def append_section_element(parent: etree.Element, section: RenoSection):
        section_div = etree.Element("div", {"class": "reno-section"})
        match section.level:
            case 1:
                section_h = etree.Element("h4")
            case 2:
                section_h = etree.Element("h5")
            case 3:
                section_h = etree.Element("h6")
            case _:
                raise ValueError(f"Unsupported section level: {section.level}")
        section_h.text = section.title or section.name
        section_div.append(section_h)
        parent.append(section_div)

        for note in section.notes:
            RenoReleaseNotesBlockProcessor.append_note_element(section_div, note)

    @staticmethod
    def append_version_element(parent: etree.Element, reno_version: RenoVersion):
        version_div = etree.Element("div", {"class": "reno-version"})
        version_h3 = etree.Element("h3")
        version_h3.text = reno_version.version
        version_div.append(version_h3)
        parent.append(version_div)

        for reno_section in reno_version.sections():
            if reno_section.is_prelude:
                RenoReleaseNotesBlockProcessor.append_prelude_element(
                    version_div, reno_section.notes
                )
            else:
                RenoReleaseNotesBlockProcessor.append_section_element(
                    version_div,
                    reno_section,
                )

    def build_release_notes_element(self) -> etree.Element:
        div = etree.Element("div", {"class": "reno-release-notes"})
        h2 = etree.Element("h2")
        h2.text = self.title
        div.append(h2)

        with open_reno_repository(
            self.repo_root, self.release_notes_dir
        ) as reno_repository:
            for version in reno_repository.versions():
                self.append_version_element(div, version)

        return div

    def test(self, parent: etree.Element, block: str) -> bool:
        return block.strip().startswith(
            "::: reno-release-notes"
        ) or block.strip().startswith(":::reno-release-notes")

    def run(self, parent: etree.Element, blocks: list[str]) -> bool:
        reno_element = self.build_release_notes_element()
        parent.append(reno_element)
        blocks.pop(0)

        return True


class RenoReleaseNotesExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {
            "repo_root": [".", "Path to the root of the repository"],
            "release_notes_dir": [
                None,
                "Directory name of the release notes directory",
            ],
            "title": ["Release Notes", "Title for the release notes section"],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md: Markdown):
        md.parser.blockprocessors.register(
            RenoReleaseNotesBlockProcessor(md.parser, self.getConfigs()),
            "reno_release_notes",
            175,
        )
