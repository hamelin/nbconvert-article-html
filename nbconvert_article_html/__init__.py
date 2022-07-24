from copy import deepcopy
import logging as lg
from pathlib import Path
import re
from typing import *

from nbconvert.exporters import HTMLExporter
from nbconvert.preprocessors import Preprocessor
from nbformat import NotebookNode


log = lg.getLogger(__name__)


OutputPreprocessor = Tuple[NotebookNode, Dict]
Annotator = Callable[[NotebookNode, Dict], OutputPreprocessor]


class CollectorAbstract(Preprocessor):
    
    def preprocess_cell(
        self,
        cell: NotebookNode,
        resources: Dict,
        index: int
    ) -> OutputPreprocessor:
        if cell.cell_type.lower() == "markdown" and (
            "abstract" in [t.lower() for t in cell.metadata.get("tags", [])]
        ):
            resources.setdefault("abstract", []).append("".join(cell.source))
        return cell, resources

    
REFERABLE = {
    "note": {
        "ref": "<sup>{}</sup>",
        "annotation": ".:cut"
    },
    "fig": {
        "ref": {
            "en": "Figure {}",
            "fr": "figure {}"
        },
        "annotation": ".:legend"
    },
    "tab": {
        "ref": {
            "en": "Table {}",
            "fr": "tableau {}"
        },
        "annotation": ".:legend"
    },
    "eq": {
        "ref": {
            "en": "Equation {}",
            "fr": "e&#769;quation {}"
        },
        "annotation": ".:margin"
    },
    "sec": {
        "ref": {
            "en": "Section {}",
            "fr": "section {}"
        },
        "hierarchy": r"^(?P<count>#+)",
        "annotation": ".:number"
    }
}


NUM_LEVELS_COUNTER_HIERARCHY = 10


class CollectorLabels(Preprocessor):
    
    def preprocess_cell(
        self,
        cell: NotebookNode,
        resources: Dict,
        index: int
    ) -> OutputPreprocessor:
        for c, label in cell["metadata"].get("label", {}).items():
            counters = resources.setdefault("counters", {})
            if c not in counters:
                counters[c] = [0] * NUM_LEVELS_COUNTER_HIERARCHY
            counter = counters[c]
            if rx := REFERABLE.get(c, {}).get("hierarchy", ""):
                if m := re.match(rx, cell["source"]):
                    g = m.groupdict()
                    if "count" in g:
                        i = len(g["count"])
                    elif "number" in g:
                        i = int(g["number"])
                    else:
                        raise ValueError(
                            f"The regular expression `{rx}' used to express how to "
                            "derive the hierarchical counter level is invalid. Its match "
                            "must return either a group of name `count' or a group of "
                            "name `number'."
                        )
                else:
                    log.error(
                        f"For cell {index}, the numbering is hierarchical, but the "
                        "convention for deducing the counter level is not "
                        "followed properly. Defaulting to the root counter."
                    )
                    i = 1
            else:
                # Non-hierarchical counter, always use the root.
                i = 1

            counter[i - 1] += 1
            number = ".".join(str(n) for n in counter[:i])
            for j in range(i, NUM_LEVELS_COUNTER_HIERARCHY):
                counter[j] = 0
            resources.setdefault("labels", {}).setdefault(c, {})[label] = number
        return cell, resources
    
    
class SolverRefs(Preprocessor):
    
    def preprocess_cell(
        self,
        cell: NotebookNode,
        resources: Dict,
        index: int
    ) -> OutputPreprocessor:
        return 

    
class AnnotatorLabeledCells(Preprocessor):
    
    def preprocess_cell(
        self,
        cell: NotebookNode,
        resources: Dict,
        index: int
    ) -> OutputPreprocessor:
        return cell, resources

    
class TaggerClass(Preprocessor):
    
    def preprocess_cell(
        self,
        cell: NotebookNode,
        resources: Dict,
        index: int
    ) -> OutputPreprocessor:
        return cell, resources

    
class ArticleExporter(HTMLExporter):

    @property
    def _dir_template_within_module(self) -> Path:
        return Path(__file__).parent / "template"

    @property
    def extra_template_basedirs(self):
        return super()._default_extra_template_basedirs() + [
            str(self._dir_template_within_module)
        ]

    def _template_name_default(self):
        for p in self._dir_template_within_module.iterdir():
            if p.is_dir():
                return p.name
        assert False, "Why is the template not where expected?"
