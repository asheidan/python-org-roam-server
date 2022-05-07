#!/usr/bin/env python3

import asyncio
import os.path

import tornado.ioloop
import tornado.web

ENTRY_DIRECTORY = "/home/emil/Brain/"
# https://github.com/ttscoff/MarkedCustomStyles/blob/master/Bear.css
STYLE_PATH = os.path.join(ENTRY_DIRECTORY, "Bear.css")


async def convert_org_to_html(path: str):
    """Async convert org to html and return string.
    
    https://docs.python.org/3/library/asyncio-subprocess.html
    """
    cmd = [
        "--standalone",
        "--shift-heading-level-by=1",
        "--wrap=preserve",
        "--css=/style.css",
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


class OrgHandler(tornado.web.RequestHandler):
    async def get(self, entry: str) -> None:

        entry_path = os.path.join(ENTRY_DIRECTORY, entry)
        stdout = await convert_org_to_html(entry_path)

        self.write(stdout)


def make_app() -> tornado.web.Application:
    url = tornado.web.url

    return tornado.web.Application([
        url(r"/style.css()", tornado.web.StaticFileHandler,
            {"path": STYLE_PATH}),
        url(r"/entries/(?P<entry>.*)", handler=OrgHandler, name="entries"),
    ])


def main() -> None:
    application = make_app()
    application.listen(8080)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()