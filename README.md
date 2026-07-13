# reno-markdown

A [Python-Markdown](https://python-markdown.github.io/) extension that renders
[Reno](https://docs.openstack.org/reno/) release notes directly into your
Markdown documents.

`reno-markdown` reads the release notes stored in your repository with Reno and
expands a marker into a fully structured release notes section — versions,
preludes, and categorized notes — as part of your normal documentation build. It
works with any Python-Markdown based site generator, including
[MkDocs](https://www.mkdocs.org/) and [Zensical](https://zensical.org/).

## Features

- Generates release notes from your Reno data at build time.
- Groups notes by version, prelude, and section (features, issues, upgrades, etc.).
- Adds `data-reno-filename` and `data-reno-sha` attributes to each note for
  traceability back to the source file and commit.

## Installation

uv
```bash
uv add --group dev reno-markdown
```

## Configuration

## Usage

### 1. Add the marker

Place the following marker in any Markdown document where you want the release
notes to appear:

```markdown
::: reno-release-notes
:::
```

At build time, the marker is replaced with the rendered release notes.

### 2. Enable the extension

Register the extension with your Markdown processor using its entry-point name
`reno_release_notes`.

**Python-Markdown**

```python
import markdown

html = markdown.markdown(
    text,
    extensions=["reno_release_notes"],
    extension_configs={
        "reno_release_notes": {
            "title": "Release Notes",
            "repo_root": ".",
            "release_notes_dir": "releasenotes",
        },
    },
)
```

**MkDocs** (`mkdocs.yml`)

```yaml
markdown_extensions:
  - reno_release_notes:
      title: Release Notes
```

**Zensical** (`zensical.toml`)

```toml
[project.markdown_extensions.reno_release_notes]
```

## Configuration

| Option              | Default         | Description                               |
| ------------------- | --------------- | ----------------------------------------- |
| `title`             | `Release Notes` | Title rendered above the generated notes. |
| `repo_root`         | `.`             | Path to the root of the repository.       |
| `release_notes_dir` | `None`          | Name of the Reno release notes directory. |

## Output structure

The extension emits a nested set of `div` elements with predictable class names
so you can style the output to match your site:

- `.reno-release-notes` — wrapper for the whole section
- `.reno-version` — a single release version
- `.reno-prelude` — the version's prelude text
- `.reno-section` — a category of notes (e.g. features, issues, upgrades)
- `.reno-note` — an individual note, annotated with `data-reno-filename` and
  `data-reno-sha`

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install dependencies
uv sync

# Run the tests
uv run pytest

# Lint
uv run ruff check
```

## License

See [LICENSE.md](LICENSE.md).

