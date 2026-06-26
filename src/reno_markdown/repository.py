from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Generator, Protocol

from reno.config import Config
from reno.loader import Loader


class Section(StrEnum):
    prelude = "prelude"
    features = "features"
    issues = "issues"
    upgrade = "upgrade"
    deprecations = "deprecations"
    critical = "critical"
    security = "security"
    fixes = "fixes"
    other = "other"


@dataclass(frozen=True)
class Note:
    sha: str
    filename: str
    note: str

    def __str__(self) -> str:
        return self.note


@dataclass(frozen=True)
class RenoSection:
    section: Section
    notes: list[Note]


class RenoVersion:
    def __init__(self, loader: Loader, version: str):
        self._loader = loader
        self._version = version

    def sections(self) -> Generator[RenoSection, None, None]:
        version_notes: dict[Section, list[Note]] = defaultdict(list)

        for filename, sha in self._loader[self._version]:
            for section, notes in self._loader.parse_note_file(filename, sha).items():
                if isinstance(notes, list):
                    for note in notes:
                        version_notes[Section(section)].append(Note(sha=sha.decode(), filename=filename, note=note))
                else:
                    version_notes[Section(section)].append(Note(sha=sha.decode(), filename=filename, note=notes))

        for section, notes in version_notes.items():
            yield RenoSection(section, notes)

    @property
    def version(self) -> str:
        return self._version


class RenoRepository:
    def __init__(self, loader: Loader):
        self._loader = loader

    def versions(self) -> Generator[RenoVersion, None, None]:
        for version in self._loader.versions:
            yield RenoVersion(self._loader, version)


@contextmanager
def open_reno_repository(repo_root: Path) -> Generator[RenoRepository, None, None]:
    with Loader(Config(str(repo_root))) as loader:
        yield RenoRepository(loader)
