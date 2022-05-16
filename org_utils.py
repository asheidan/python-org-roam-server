import asyncio
import re
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import pandoc
import pandoc.types

from settings import STYLE_PATH


# TODO: brew link python@3.10
# TODO: byt till 3.10
# TODO: manuellt länka in python3.9 och kanske pip3.9


async def convert_org_to_html_old(path: str, *, after_body: Optional[bytes] = None, standalone: bool = True):  # {{{
    """Async convert org to html and return string.
    
    https://docs.python.org/3/library/asyncio-subprocess.html
    """
    cmd = (["--standalone"] if standalone else []) + [
        "--shift-heading-level-by=1",
        "--wrap=preserve",
        "--no-highlight",
        "--include-before-body=templates/org-nav.html",
        "--css=/style.css",
        "--from=org",
        "--to=html",
        path,
    ] + (["--include-after-body=/dev/stdin"] if after_body else [])
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

def convert_org_to_html(file=None, source=None,
                        relative_to=None, shift_heading: int = 1,
                        ) -> Tuple[Dict[str, str], str]:
    """Convert org to html returning metadata, body.
    """
    # TODO: Implement `relative_to` to enable correct backlinks from entries in subdirectories
    # TODO: Implement using highlight.js
    options = [
        "--no-highlight",
        f"--shift-heading-level-by={shift_heading}",
        "--wrap=preserve",
    ]
    types = pandoc.types
    document = pandoc.read(file=file, source=source, format="org")

    raw_blocks = []
    match document:
        case types.Pandoc(_, list(body)):
            for element in body:
                match element:
                    case types.RawBlock(types.Format('org'), content):
                        raw_blocks.append(content)

                    case types.DefinitionList(list(list_entries)):
                        #print(raw_blocks)
                        #print(list_entries)
                        for block in raw_blocks:
                            key, value = block[2:].split(": ", maxsplit=1)
                            list_entries.append(([types.Str(key)],
                                                 [[types.Plain([types.Str(value)])]]))

                    case _:
                        break

    match document:
        case types.Pandoc(types.Meta(meta_dict)):
            metadata = {key: pandoc.write(metainline[0]).strip()
                        for key, metainline in meta_dict.items()}
            #print(metadata)

            return metadata, pandoc.write(document, format="html", options=options)

def point_in_org(path: str, points: List[int]):  #{{{

    points = sorted(points, reverse=True)

    levels = []
    current_level = 0
    current_point = points.pop()

    current_offset = 0

    found_lines = []
    
    for line in open(path, "r"):

        current_offset += len(line)
        #print(current_offset)

        if current_offset > current_point:
            #print(levels)
            #print(repr(line))
            #print(current_offset)

            found_lines.append(convert_org_to_html(source=line.strip())[1])

            if points:
                current_point = points.pop()
            else:
                break

        if line[0] == "*":
            header_marker, _ = re.split(r"[^*]", line, maxsplit=1)
            #print(header_marker)
            del levels[len(header_marker) - 1:]
            levels.append(line.strip())

    return found_lines
#}}}
