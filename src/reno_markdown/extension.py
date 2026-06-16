from dataclasses import dataclass
from typing import Generator
import xml.etree.ElementTree as etree
from markdown import Extension
from markdown.treeprocessors import Treeprocessor


@dataclass
class ElementLocation:
    node: etree.Element
    parent: etree.Element
    index: int


def iter_parent_child(root: etree.Element) -> Generator[ElementLocation, None, None]:
    for index, child in enumerate(root):
        yield from iter_parent_child(child)
        yield ElementLocation(node=child, parent=root, index=index)


class RenoReleaseNotesTreeProcessor(Treeprocessor):
    def build_release_notes_element(self) -> etree.Element:
        div = etree.Element("div", {"class": "reno-release-notes"})
        div.append(etree.Element("p", text="Release notes will be generated here."))

        return div

    def run(self, root: etree.Element):
        for element in iter_parent_child(root):
            if element.node.text and element.node.text.strip() == "[release-notes]":
                reno_element = self.build_release_notes_element()

                element.parent.remove(element.node)
                element.parent.insert(element.index, reno_element)

        return None


class RenoReleaseNotesExtension(Extension):
    def __init__(self, title: str = "Release Notes"):
        self.title = title

    def extendMarkdown(self, md):
        md.treeprocessors.register(RenoReleaseNotesTreeProcessor(md), "reno_release_notes", 15)
