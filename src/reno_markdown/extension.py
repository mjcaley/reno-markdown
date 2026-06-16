from typing import Generator
import xml.etree.ElementTree as etree
from markdown import Extension
from markdown.treeprocessors import Treeprocessor


def iter_parent_child(root: etree.Element) -> Generator[tuple[etree.Element, etree.Element], None, None]:
    for child in root:
        yield from iter_parent_child(child)
        yield root, child


class RenoReleaseNotesTreeProcessor(Treeprocessor):
    def build_release_notes_element(self) -> etree.Element:
        div = etree.Element("div", {"class": "reno-release-notes"})
        div.append(etree.Element("p", text="Release notes will be generated here."))

        return div

    def run(self, root: etree.Element):
        for parent, child in iter_parent_child(root):
            if child.text and child.text.strip() == "[release-notes]":
                new_el = self.build_release_notes_element()

                idx = list(parent).index(child)
                parent.remove(child)
                parent.insert(idx, new_el)

        return None


class RenoReleaseNotesExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(RenoReleaseNotesTreeProcessor(md), "reno_release_notes", 15)
