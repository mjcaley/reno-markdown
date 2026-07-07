from dataclasses import dataclass

from reno_markdown.repository import RenoVersion


@dataclass
class FakeSection:
    name: str
    title: str | None = None


def test_version_yields_section():
    class MockLoader:
        def __getitem__(self, version):
            return [("file1", b"sha1")]

        def parse_note_file(self, filename, sha):
            return {"singlenote": ["note0"], "multinote": ["note1", "note2"]}

        @property
        def versions(self):
            return ["v1.0.0"]

    class MockConfig:
        prelude_section_name = "prelude"
        sections = [
            FakeSection("prelude", None),
            FakeSection("singlenote", "Single Note Section"),
            FakeSection("multinote", "Multiple Note Section"),
        ]

    loader = MockLoader()
    config = MockConfig()
    version = RenoVersion(loader, config, "v1.0.0")

    sections = list(version.sections())

    assert len(sections) == 2

    assert sections[0].name == "singlenote"
    assert len(sections[0].notes) == 1
    assert sections[0].notes[0].note == "note0"

    assert sections[1].name == "multinote"
    assert len(sections[1].notes) == 2
    assert sections[1].notes[0].note == "note1"
    assert sections[1].notes[1].note == "note2"


def test_version_with_prelude():
    class MockLoader:
        def __getitem__(self, version):
            return [("file1", b"sha1")]

        def parse_note_file(self, filename, sha):
            return {"prelude": ["note0"], "singlenote": ["note0"]}

        @property
        def versions(self):
            return ["v1.0.0"]

    class MockConfig:
        prelude_section_name = "prelude"
        sections = [
            FakeSection("prelude", None),
            FakeSection("singlenote", "Single Note Section"),
        ]

    loader = MockLoader()
    config = MockConfig()
    version = RenoVersion(loader, config, "v1.0.0")

    sections = list(version.sections())

    assert len(sections) == 2

    assert sections[0].name == "prelude"
    assert len(sections[0].notes) == 1
    assert sections[0].notes[0].note == "note0"

    assert sections[1].name == "singlenote"
    assert len(sections[1].notes) == 1
    assert sections[1].notes[0].note == "note0"
