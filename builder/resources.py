from __future__ import annotations

import dataclasses
import functools
import logging

from pathlib import Path
from typing import ClassVar
from xml.etree import ElementTree as ET

from document import Document
from util import sluggify, is_wide


def make_headline_image(src: str, alt: str, wide: bool = False) -> ET.Element:
    """ make an `img.headline` element with the given src and alt text, and optionally the 'wide' class. """
    img = ET.Element('img')
    img.set('src', str(src))
    img.set('alt', alt)
    if wide:
        img.set('class', 'wide')
    else:
        img.set('class', 'tall')
    return img


@dataclasses.dataclass
class Resource:
    DIRECTORY: ClassVar[Path]
    """ relative path to output directory (should be set by subclasses, e.g. pieces/ or projects/) """
    path: Path
    """ Piece directory """
    slug: str = None
    """ Piece slug, defaults to directory name """
    _description_path: Path = None
    description_path: dataclasses.InitVar[Path] = None
    """ Path to description file, defaults to slug.md or index.md """

    def __post_init__(self, description_path: Path = None):
        if not self.slug:
            self.slug = sluggify(self.path.stem)
        if description_path is not None:
            self._description_path = description_path


    @classmethod
    def from_path(cls, path: Path):
        if path.suffix in ('.md', '.html'):
            return cls(path.parent, description_path=path)
        else:
            return cls(path)

    @functools.cached_property
    def assets(self) -> list[Path]:
        return [p for p in self.path.iterdir() if p.suffix not in ('.md', '.html', '')]

    @functools.cached_property
    def description_path(self) -> Path | None:
        if (p := self.path / 'index.md').exists():
            return p
        if (p := self.path / f'{self.slug}.md').exists():
            return p
        if p := next(self.path.glob('.md'), None):
            return p
        return None


    @functools.cached_property
    def description(self) -> Document:
        if not self.description_path:
            logging.debug('generating default description for %s/%s', self.DIRECTORY, self.slug)
            return self._generate_description()
        return Document.load_file(self.description_path)

    def _generate_description(self) -> Document:
        """ generate a simple description document for when no index.md is present. """
        body = ET.fromstring(f'<html><section><h1>{self.slug}</h1></section></html>')

        if not self.assets:
            headline_img = None
        else:
            path = next((p for p in self.assets if sluggify(p.stem) == self.slug), self.assets[0])
            headline_img = make_headline_image(str(path.relative_to(self.path)), alt=str(path.stem), wide=is_wide(path))
            div = body.makeelement('div', {'class': 'headline'})
            div.append(headline_img)
            body.insert(0, div)

        return Document(
            self.slug,
            body,
            primary_image=headline_img
        )


@dataclasses.dataclass
class Piece(Resource):
    DIRECTORY: ClassVar[Path] = Path('pieces')


@dataclasses.dataclass
class Project(Resource):
    DIRECTORY: ClassVar[Path] = Path('projects')