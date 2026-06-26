from dataclasses import dataclass
from pathlib import Path

import pytest
from dulwich import porcelain

GIT_AUTHOR = "John Smith <jsmith@example.com>".encode()


@dataclass
class MockRepo:
    root: Path
    notes: list[Path]


@pytest.fixture
def mock_repo(tmp_path):
    repo_dir = tmp_path / "mock_repo"
    porcelain.init(str(repo_dir))

    notes_dir = repo_dir / "releasenotes" / "notes"
    notes_dir.mkdir(parents=True)
    bug_note = notes_dir / "fixes-82e2c49428491510.yaml"
    bug_note.write_text("""---
fixes:
- A mock bug fix.""")
    porcelain.add(repo_dir, bug_note)
    porcelain.commit(repo_dir, "Add note for bug fix", GIT_AUTHOR, sign=False)
    porcelain.tag_create(repo_dir, "v1.0.0")

    yield MockRepo(root=repo_dir, notes=[bug_note.relative_to(repo_dir)])
