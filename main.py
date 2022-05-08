#!/usr/bin/env python3

import asyncio
import os.path
from typing import Optional

import aiosqlite
import tornado.ioloop
import tornado.web

ENTRY_DIRECTORY = os.path.expanduser("~/Brain/")
# https://github.com/ttscoff/MarkedCustomStyles/blob/master/Bear.css
STYLE_PATH = os.path.join(ENTRY_DIRECTORY, "Bear.css")

# TODO: Async DB-connection
# https://pypi.org/project/aiosqlite/

# TODO: argparse


async def convert_org_to_html(path: str):  # {{{
    """Async convert org to html and return string.
    
    https://docs.python.org/3/library/asyncio-subprocess.html
    """
    cmd = [
        "--standalone",
        "--shift-heading-level-by=1",
        "--wrap=preserve",
        "--css=/style.css",
        "--from=org",
        "--to=html",
        path,
    ]
    process = await asyncio.create_subprocess_exec(
        "pandoc",
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

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

#}}}



# Controllers {{{
class OrgHandler(tornado.web.RequestHandler):  # {{{
    async def get(self, entry: str) -> None:

        entry_path = os.path.join(ENTRY_DIRECTORY, entry)
        stdout = await convert_org_to_html(entry_path)

        self.write(stdout)
# }}}
class OrgListHandler(tornado.web.RequestHandler):  # {{{
    async def get(self) -> None:
        db = await db_connection()
        sql_string = """SELECT
            TRIM(title, '"') AS title,
            REPLACE(TRIM(file, '"'),?,'') AS file
        FROM titles;"""
        async with db.execute(sql_string, (ENTRY_DIRECTORY,)) as cursor:
            entries = await cursor.fetchall()
            self.render("org-list.html.j2", entries=entries)
#}}} #}}}

def make_app() -> tornado.web.Application:
    url = tornado.web.url

    return tornado.web.Application(
        [
            url(r"/style.css()", tornado.web.StaticFileHandler,
                {"path": STYLE_PATH}),
            url(r"/entries/", handler=OrgListHandler, name="entries-list"),
            url(r"/entries/(?P<entry>.+)", handler=OrgHandler, name="entries-show"),
        ],
        template_path="templates",
    )


def main() -> None:
    application = make_app()
    application.listen(8080)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
