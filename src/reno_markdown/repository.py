from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Generator

from reno.config import Config
from reno.loader import Loader


@dataclass(frozen=True)
class Note:
    sha: str
    filename: str
    note: str

    def __str__(self) -> str:
        return self.note


@dataclass(frozen=True)
class RenoSectionPrelude:
    notes: list[Note]


@dataclass(frozen=True)
class RenoSection:
    section: str
    notes: list[Note]


class RenoVersion:
    def __init__(self, loader: Loader, config: RenoRepositoryConfig, version: str):
        self._loader = loader
        self._config = config
        self._version = version

    def sections(self) -> Generator[RenoSection, None, None]:
        prelude_notes: list[Note] = []
        version_notes: dict[str, list[Note]] = defaultdict(list)

        for filename, sha in self._loader[self._version]:
            for section, notes in self._loader.parse_note_file(filename, sha).items():
                if isinstance(notes, list):
                    for note in notes:
                        note_data = Note(sha=sha.decode(), filename=filename, note=note)
                        if section == self._config.prelude_name:
                            prelude_notes.append(note_data)
                        else:
                            version_notes[section].append(note_data)
                else:
                    note_data = Note(sha=sha.decode(), filename=filename, note=notes)
                    if section == self._config.prelude_name:
                        prelude_notes.append(note_data)
                    else:
                        version_notes[section].append(note_data)

        if prelude_notes:
            yield RenoSectionPrelude(prelude_notes)
        for section, notes in version_notes.items():
            yield RenoSection(section, notes)

    @property
    def version(self) -> str:
        return self._version


class RenoRepository:
    def __init__(self, loader: Loader, config: RenoRepositoryConfig):
        self._loader = loader
        self._config = config

    def sections(self) -> Generator[str, None, None]:
        for section in self._loader.sections:
            yield section

    def versions(self) -> Generator[RenoVersion, None, None]:
        for version in self._loader.versions:
            yield RenoVersion(self._loader, self._config, version)


class RenoRepositoryConfig:
    def __init__(self, repo_root: Path, release_notes_dir: str | None = None):
        self.reno_config = Config(str(repo_root), release_notes_dir)

    @property
    def prelude_name(self) -> str:
        return self.reno_config.prelude_section_name


@contextmanager
def open_reno_repository(repo_root: Path, release_notes_dir: str | None = None) -> Generator[RenoRepository, None, None]:
    config = RenoRepositoryConfig(repo_root, release_notes_dir)
    with Loader(config.reno_config) as loader:
        yield RenoRepository(loader, config)
