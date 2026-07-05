from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator

from reno.config import Config
from reno.loader import Loader


class RenoRepositoryConfig:
    def __init__(self, repo_root: Path, release_notes_dir: str | None = None):
        self.reno_config = Config(str(repo_root), release_notes_dir)

    @property
    def prelude_name(self) -> str:
        return self.reno_config.prelude_section_name

    def sections(self) -> list[str]:
        return [self.prelude_name] + [section.name for section in self.reno_config.sections]

    def section_title(self, section: str) -> str | None:
        for s in self.reno_config.sections:
            if s.name == section:
                return s.title


@dataclass(frozen=True)
class Note:
    sha: str
    filename: str
    note: str

    def __str__(self) -> str:
        return self.note


@dataclass(frozen=True)
class RenoSection:
    name: str
    title: str | None
    level: int = 1
    notes: list[Note] = field(default_factory=list)
    is_prelude: bool = False

    def __hash__(self) -> int:
        return hash(self.name)


class RenoVersion:
    def __init__(self, loader: Loader, config: RenoRepositoryConfig, version: str):
        self._loader = loader
        self.config = config
        self._version = version

    def sections(self) -> Generator[RenoSection, None, None]:
        version_notes = {section: [] for section in self.config.sections()}

        for filename, sha in self._loader[self._version]:
            for section, notes in self._loader.parse_note_file(filename, sha).items():
                if isinstance(notes, list):
                    for note in notes:
                        note_data = Note(sha=sha.decode(), filename=filename, note=note)
                        version_notes[section].append(note_data)
                else:
                    note_data = Note(sha=sha.decode(), filename=filename, note=notes)
                    version_notes[section].append(note_data)

        if version_notes[self.config.prelude_name]:
            yield RenoSection(self.config.prelude_name, None, notes=version_notes[self.config.prelude_name], is_prelude=True)
        for section, notes in version_notes.items():
            if section != self.config.prelude_name:
                yield RenoSection(section, self.config.section_title(section), notes=notes)

    @property
    def version(self) -> str:
        return self._version


class RenoRepository:
    def __init__(self, loader: Loader, config: RenoRepositoryConfig):
        self._loader = loader
        self.config = config

    def versions(self) -> Generator[RenoVersion, None, None]:
        for version in self._loader.versions:
            yield RenoVersion(self._loader, self.config, version)


@contextmanager
def open_reno_repository(repo_root: Path, release_notes_dir: str | None = None) -> Generator[RenoRepository, None, None]:
    config = RenoRepositoryConfig(repo_root, release_notes_dir)
    with Loader(config.reno_config) as loader:
        yield RenoRepository(loader, config)
