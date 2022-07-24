from pathlib import Path
from typing import *  # noqa


from nbconvert import HTMLExporter
from traitlets.config import Config


def export_notebook(name: str, config: Config) -> Tuple[str, Dict]:
    return HTMLExporter(config=config).from_filename(
        Path(__file__).parent / "notebooks" / name
    )
