#!/usr/bin/env python3

import asyncio
import os.path
from dataclasses import dataclass
from typing import List
from typing import Optional
from typing import Sequence

import aiosqlite
import tornado.ioloop
import tornado.web

from lisp_parser import parse as lisp_parser

ORG_DB_PATH = os.path.expanduser("~/.emacs.d/.local/etc/org-roam.workaround.db")
ENTRY_DIRECTORY = os.path.expanduser("~/Brain/")
# https://github.com/ttscoff/MarkedCustomStyles/blob/master/Bear.css
STYLE_PATH = os.path.join('static', "Bear.css")

# TODO: Async DB-connection
# https://pypi.org/project/aiosqlite/

# TODO: argparse


async def convert_org_to_html(path: str, input: Optional[bytes] = None):  # {{{
    """Async convert org to html and return string.
    
    https://docs.python.org/3/library/asyncio-subprocess.html
    """
    cmd = [
        "--standalone",
        "--shift-heading-level-by=1",
        "--wrap=preserve",
        "--no-highlight",
        "--include-before-body=templates/org-nav.html",
        "--css=/style.css",
        "--from=org",
        "--to=html",
        path,
    ] + (["--include-after-body=/dev/stdin"] if input else [])
    process = await asyncio.create_subprocess_exec(
        "pandoc",
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate(input=input)

    if stderr:
        print(stderr)

    return stdout
#}}}


_db_connection: Optional[aiosqlite.core.Connection] = None
async def db_connection() -> aiosqlite.core.Connection:
    global _db_connection

    if _db_connection is not None:
        return _db_connection

    _db_connection = await aiosqlite.connect(ORG_DB_PATH)
    _db_connection.row_factory = aiosqlite.Row

    return _db_connection


# Models {{{
# class Backlink {{{
@dataclass
class Backlink:
    source: str
    title: str
    outline: List[str]
    point: Optional[int]

    @classmethod
    def list_as_tree(cls, backlinks: Sequence):
        from collections import OrderedDict
        tree = OrderedDict()

        for link in backlinks:
            levels = [link.title, *link.outline]
            node = tree
            for level in levels[:-1]:
                if level not in node:
                    node[level] = OrderedDict()

                node = node[level]

            node[levels[-1]] = link

        from pprint import pprint
        pprint(tree)

        return tree
#}}}
# class Entry {{{
@dataclass
class Entry:
    title: str
    file: str

    @property
    def path(self) -> str:
        return os.path.join(ENTRY_DIRECTORY, self.file)

    async def backlinks(self, ) -> Sequence:
        db = await db_connection()
        sql_string = """SELECT
            REPLACE(TRIM(source, '"'), ?, '') AS source,
            TRIM(titles.title, '"') AS title,
            properties
        FROM links
            LEFT JOIN titles ON links.source = titles.file
        WHERE type = '"file"' AND dest = ?"""
        query = db.execute(sql_string, (
            ENTRY_DIRECTORY,
            f'"{self.path}"',
        ),)
        async with query as cursor:
            links = await cursor.fetchall()

        return [Backlink(source=link['source'], title=link['title'],
                         **lisp_parser(link['properties']))
                for link in links]

    @classmethod
    async def list(cls):
        db = await db_connection()
        sql_string = """SELECT
            TRIM(title, '"') AS title,
            REPLACE(TRIM(file, '"'),?,'') AS file
        FROM titles;"""
        query = db.execute(sql_string, (ENTRY_DIRECTORY,))
        async with query as cursor:
            entries = await cursor.fetchall()

        return [cls(**entry) for entry in entries]
#}}} #}}}


# Controllers {{{
class OrgHandler(tornado.web.RequestHandler):  # {{{
    async def get(self, entry: str) -> None:
        # FIXME: Prevent directory traversal
        # TODO: Make backlinks into tree-structure
        # (Same file should only have one top level entry)

        instance = Entry(title="", file=entry)

        endmatter = None
        backlinks = await instance.backlinks()
        if backlinks:
            endmatter = self.render_string("org-backlinks.html", backlinks=backlinks)
        stdout = await convert_org_to_html(instance.path, endmatter)

        self.write(stdout)
# }}}
class OrgListHandler(tornado.web.RequestHandler):  # {{{
    async def get(self) -> None:
        # TODO: Add tags to list
        entries = await Entry.list()
        self.render("org-list.html", entries=entries)
#}}} #}}}

def make_app() -> tornado.web.Application:
    url = tornado.web.url

    return tornado.web.Application(
        [
            url(r"/style.css()", tornado.web.StaticFileHandler,
                {"path": STYLE_PATH}),
            url(r"/entries/", handler=OrgListHandler, name="entry-list"),
            url(r"/entries/(?P<entry>.+)", handler=OrgHandler, name="entry-show"),
        ],
        template_path="templates",
    )


def main() -> None:
    application = make_app()
    application.listen(8080)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
