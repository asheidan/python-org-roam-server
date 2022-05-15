#!/usr/bin/env python3

import os.path
from typing import List
from typing import Optional
from typing import Sequence

import tornado.ioloop
import tornado.web

from controllers import OrgHandler
from controllers import OrgListHandler
from lisp_parser import parse as lisp_parser
from settings import STYLE_PATH


# TODO: argparse


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
