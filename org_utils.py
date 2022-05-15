import asyncio
from typing import Optional

from settings import STYLE_PATH


async def convert_org_to_html(path: str, input: Optional[bytes] = None):  # {{{
    """Async convert org to html and return string.
    
    https://docs.python.org/3/library/asyncio-subprocess.html
    """
    cmd = [
        "--standalone",
        "--shift-heading-level-by=1",
        "--wrap=preserve",
        "--no-highlight",
        "--include-before-body=templates/org-nav.html",  # TODO: this should not be controlled/implmented here
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

