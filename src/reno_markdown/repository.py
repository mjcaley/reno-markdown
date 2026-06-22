from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Generator, Protocol

from reno.config import Config
from reno.loader import Loader


class RenoRepositoryProtocol(Protocol):
    def versions(self) -> Generator[str, None, None]:
        ...

    def sections(self, version: str) -> Generator["Section", None, None]:
        ...


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


class RenoRepository:
    def __init__(self, repo_root: Path):
        self.config = Config(str(repo_root))

    def versions(self) -> Generator[str, None, None]:
        with Loader(self.config) as loader:
            yield from loader.versions

    def sections(self, version: str) -> Generator[tuple[Section, list[Note]], None, None]:
        version_notes: dict[Section, list[Note]] = defaultdict(list)

        with Loader(self.config) as loader:
            for filename, sha in loader[version]:
                for section, notes in loader.parse_note_file(filename, sha).items():
                    if isinstance(notes, list):
                        for note in notes:
                            # breakpoint()
                            version_notes[Section(section)].append(Note(sha=sha, filename=filename, note=note))
                    else:
                        version_notes[Section(section)].append(Note(sha=sha, filename=filename, note=notes))

        for section, notes in version_notes.items():
            yield section, notes
