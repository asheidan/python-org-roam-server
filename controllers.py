import tornado.web

from models import Backlink
from models import Entry
from org_utils import convert_org_to_html

class OrgHandler(tornado.web.RequestHandler):  # {{{
    async def get(self, entry: str) -> None:
        # FIXME: Prevent directory traversal
        # TODO: Make backlinks into tree-structure
        # (Same file should only have one top level entry)

        instance = Entry(title="", file=entry)

        endmatter = None
        backlinks = await instance.backlinks()
        if backlinks:
            backlink_count = len(backlinks)
            backlink_tree = Backlink.list_as_tree(backlinks)
            endmatter = self.render_string("org-backlinks.html",
                                           backlink_tree=backlink_tree,
                                           backlink_count=backlink_count)
        stdout = await convert_org_to_html(instance.path, endmatter)

        self.write(stdout)
# }}}
class OrgListHandler(tornado.web.RequestHandler):  # {{{
    async def get(self) -> None:
        # TODO: Add tags to list
        entries = await Entry.list()
        self.render("org-list.html", entries=entries)
#}}}
