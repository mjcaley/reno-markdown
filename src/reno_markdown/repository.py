from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, Protocol, Sequence

from reno.config import Config
from reno.loader import Loader


class RenoLoaderProtocol(Protocol):
    def __getitem__(self, version: str) -> list[tuple[str, bytes]]: ...

    def parse_note_file(self, filename: str, sha: bytes) -> dict[str, list[str]]: ...

    @property
    def versions(self) -> list[str]: ...


class SectionProtocol(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def title(self) -> str | None: ...


class RenoConfigurationProtocol(Protocol):
    @property
    def prelude_section_name(self) -> str: ...

    @property
    def sections(self) -> Sequence[SectionProtocol]: ...


class RenoConfigurationAdapter:
    def __init__(self, config: Config):
        self.reno_config = config

    @property
    def prelude_section_name(self) -> str:
        return self.reno_config.prelude_section_name
    
    @property
    def sections(self) -> Sequence[SectionProtocol]:
        return self.reno_config.sections


def all_sections(config: RenoConfigurationProtocol) -> list[str]:
    return [config.prelude_section_name] + [section.name for section in config.sections]


def section_title(config: RenoConfigurationProtocol, section: str) -> str | None:
    for s in config.sections:
        if s.name == section:
            return s.title


@dataclass(frozen=True)
class Note:
    sha: str
    filename: str
    note: str


@dataclass(frozen=True)
class RenoSection:
    name: str
    title: str | None
    level: int = 1
    notes: list[Note] = field(default_factory=list)
    is_prelude: bool = False


class RenoVersion:
    def __init__(
        self,
        loader: RenoLoaderProtocol,
        config: RenoConfigurationProtocol,
        version: str,
    ):
        self._loader = loader
        self.config = config
        self._version = version

    def sections(self) -> Generator[RenoSection, None, None]:
        version_notes = {section: [] for section in all_sections(self.config)}

        for filename, sha in self._loader[self._version]:
            for section, notes in self._loader.parse_note_file(filename, sha).items():
                for note in notes:
                    note_data = Note(sha=sha.decode(), filename=filename, note=note)
                    version_notes[section].append(note_data)
        if version_notes[self.config.prelude_section_name]:
            yield RenoSection(
                self.config.prelude_section_name,
                None,
                notes=version_notes[self.config.prelude_section_name],
                is_prelude=True,
            )
        for section, notes in version_notes.items():
            if section != self.config.prelude_section_name:
                yield RenoSection(
                    section, section_title(self.config, section), notes=notes
                )

    @property
    def version(self) -> str:
        return self._version


class RenoRepository:
    def __init__(self, loader: RenoLoaderProtocol, config: RenoConfigurationProtocol):
        self._loader = loader
        self.config = config

    def versions(self) -> Generator[RenoVersion, None, None]:
        for version in self._loader.versions:
            yield RenoVersion(self._loader, self.config, version)


@contextmanager
def open_reno_repository(
    repo_root: Path, release_notes_dir: str | None = None
) -> Generator[RenoRepository, None, None]:
    reno_config = Config(str(repo_root), release_notes_dir)
    with Loader(reno_config) as loader:
        config_adaptor = RenoConfigurationAdapter(reno_config)
        yield RenoRepository(loader, config_adaptor)
