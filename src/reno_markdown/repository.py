"""Abstraction for Reno repository, version, and release notes.

Provides a context manager and iterators for Reno data."""

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
    """Interface for a Reno configuration wrapper."""

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
    """List the name for all Reno sections including the prelude.

    Args:
        config: A Reno configuration.

    Returns:
        A list of all Reno sections starting with the 'prelude' section name.
    """

    return [config.prelude_section_name] + [section.name for section in config.sections]


def section_title(config: RenoConfigurationProtocol, section: str) -> str | None:
    """Returns the title of a section.

    Args:
        config: A Reno configuration.
        section: The name of the section.

    Returns:
        The title of the section, or None if not found.
    """

    for s in config.sections:
        if s.name == section:
            return s.title


@dataclass(frozen=True)
class Note:
    """A single Reno note."""

    sha: str
    filename: str
    note: str


@dataclass(frozen=True)
class RenoSection:
    """A section of Reno release notes."""

    name: str
    title: str | None
    level: int = 1
    notes: list[Note] = field(default_factory=list)
    is_prelude: bool = False


class RenoVersion:
    """A version of release notes containing all the sections and notes."""

    def __init__(
        self,
        loader: RenoLoaderProtocol,
        config: RenoConfigurationProtocol,
        version: str,
    ):
        """Constructed by a Reno loader, configuration, and version string.

        Args:
            loader: A Reno loader instance.
            config: A Reno configuration instance.
            version: A string representation of the version.
        """

        self._loader = loader
        self.config = config
        self._version = version

    def sections(self) -> Generator[RenoSection, None, None]:
        """Iterates the sections of a version.

        Yields:
            Each section of the version.
        """

        version_notes = {section: [] for section in all_sections(self.config)}

        for filename, sha in self._loader[self._version]:
            for section, notes in self._loader.parse_note_file(filename, sha).items():
                if section == self.config.prelude_section_name:
                    note_data = Note(sha=sha.decode(), filename=filename, note=notes)
                    version_notes[section].append(note_data)
                else:
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
        """A string representation of the version."""

        return self._version


class RenoRepository:
    """The interface to Reno."""

    def __init__(self, loader: RenoLoaderProtocol, config: RenoConfigurationProtocol):
        """Construct a Reno repository to interface with Reno.

        Args:
            loader: A Reno loader instance.
            config: A Reno configuration instance.
        """

        self._loader = loader
        self.config = config

    def versions(self) -> Generator[RenoVersion, None, None]:
        """Iterates the versions of release notes.

        Yields:
            An iterator over each version.
        """

        for version in self._loader.versions:
            yield RenoVersion(self._loader, self.config, version)


@contextmanager
def open_reno_repository(
    repo_root: Path, release_notes_dir: str | None = None
) -> Generator[RenoRepository, None, None]:
    """Context manager for interfacing with Reno.

    Args:
        reno_root: Path to the repository.
        release_notes_dir: Optional name of the release notes directory.

    Yields:
        A RenoRepository instance.
    """

    reno_config = Config(str(repo_root), release_notes_dir)
    with Loader(reno_config) as loader:
        config_adaptor = RenoConfigurationAdapter(reno_config)
        yield RenoRepository(loader, config_adaptor)
