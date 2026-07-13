## Installation

### Install with uv

```bash
uv add --dev reno-markdown
```

### Install with pip

```bash
pip install reno-markdown
```

## Configuration

### Zensical

When using `zensical.toml` add the following line:

```toml
[project.markdown_extensions.reno_release_notes]
```

## Usage

Place the following marker in any Markdown document where you want the release
notes to appear:

```markdown
::: reno-release-notes
:::
```

At build time, the marker is replaced with the rendered release notes.

Reno's configuration is used 
