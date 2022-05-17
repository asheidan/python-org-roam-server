import dataclasses
from typing import Dict
from typing import List
from typing import Union

import tornado.web

from models import Backlink
from models import Entry
from models import Link
from org_utils import convert_org_to_html
from org_utils import point_in_org

def replace_point_list(tree: Union[Dict, List], source = None) -> None:
    if not source:
        for _title, (source, subtree) in tree.items():
            instance = Entry(title="", file=source)
            replace_point_list(tree=subtree, source=instance.path)

        return

    if isinstance(tree, dict):
        for _title, subtree in tree.items():
            replace_point_list(tree=subtree, source=source)

        return

    elif isinstance(tree, list):
        tree[:] = point_in_org(source, points=tree)

        return

    raise ValueError("Got unknown data: %s" % tree)


class OrgHandler(tornado.web.RequestHandler):  # {{{
    async def get(self, entry: str) -> None:
        # FIXME: Prevent directory traversal
        # (Same file should only have one top level entry)

        instance = Entry(title="", file=entry)

        backlinks = await instance.backlinks()
        backlink_count = len(backlinks)
        backlink_tree = None
        if backlinks:
            backlink_tree = Backlink.list_as_tree(backlinks)
            replace_point_list(backlink_tree)

        meta, body = convert_org_to_html(file=instance.path)

        self.render("org-show.html",
                    title=meta["title"],
                    body=body,
                    backlink_count=backlink_count,
                    backlink_tree=backlink_tree)
# }}}
class OrgGraphHandler(tornado.web.RequestHandler):  # {{{
    async def get(self) -> None:
        entries = await Entry.list()
        simplified_entries = list(map(dataclasses.asdict, entries))

        links = await Link.list()
        simplified_links = list(map(dataclasses.asdict, links))

        self.render("org-graph.html", entries=simplified_entries, links=simplified_links)
#}}}
class OrgListHandler(tornado.web.RequestHandler):  # {{{
    async def get(self) -> None:
        # TODO: Add tags to list
        entries = await Entry.list()
        self.render("org-list.html", entries=entries)
#}}}
class OrgPointHandler(tornado.web.RequestHandler):  #{{{
    async def get(self, entry: str, point: int) -> None:
        print(entry, point)

        instance = Entry(title="", file=entry)
        point_in_org(instance.path, points=[int(point)])
#}}}
