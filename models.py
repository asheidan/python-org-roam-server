import os.path
from dataclasses import dataclass
from typing import List
from typing import Optional
from typing import Sequence

import aiosqlite

from lisp_parser import parse as lisp_parser
from settings import ENTRY_DIRECTORY
from settings import ORG_DB_PATH


_db_connection: Optional[aiosqlite.core.Connection] = None
async def db_connection() -> aiosqlite.core.Connection:
    global _db_connection

    if _db_connection is not None:
        return _db_connection

    _db_connection = await aiosqlite.connect(ORG_DB_PATH)
    _db_connection.row_factory = aiosqlite.Row

    return _db_connection


# class Backlink {{{
@dataclass
class Backlink:
    source: str
    title: str
    outline: List[str]
    point: Optional[int]

    @classmethod
    def list_as_tree(cls, backlinks: Sequence):
        tree = dict()

        for link in backlinks:

            if link.title not in tree:
                tree[link.title] = (link.source, dict())

            levels = link.outline or [":: Top"]
            _source, node = tree[link.title]
            for level in levels[:-1]:
                if level not in node:
                    node[level] = dict()

                node = node[level]

            if levels[-1] not in node:
                node[levels[-1]] = []

            node[levels[-1]].append(link.point)

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
#}}}


