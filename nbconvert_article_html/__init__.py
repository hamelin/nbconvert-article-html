from copy import deepcopy
from importlib import import_module
import logging as lg
from pathlib import Path
import re
import sys
from typing import *

from nbconvert.exporters import HTMLExporter
from nbconvert.preprocessors import Preprocessor
from nbformat import NotebookNode


log = lg.getLogger(__name__)


OutputPreprocessor = Tuple[NotebookNode, Dict]
Annotator = Callable[[NotebookNode, Dict, int], Tuple[Sequence[NotebookNode], Dict, int]]


def _is_cell_markdown(cell: NotebookNode) -> bool:
    return cell.cell_type.lower() == "markdown"


def _cell_tags_norm(cell: NotebookNode) -> Sequence[str]:
    return [t.lower() for t in cell.metadata.get("tags", [])]


def copy_cell(node: NotebookNode) -> NotebookNode:
    copy = deepcopy(node)
    if "id" in copy:
        del copy["id"]
    return copy


class CollectorLanguage(Preprocessor):
    
    def preprocess(self, nb: NotebookNode, resources: Dict) -> OutputPreprocessor:
        resources["language"] = nb.metadata.get("language", "") or nb.metadata.get(
            "lang",
            ""
        )
        if not resources["language"]:
            log.warning(
                "The language of this notebook is not explicitly defined in its "
                "metadata; we will assume it is English (en)"
            )
            resources["language"] = "en"
        return nb, resources
    

class CollectorAbstract(Preprocessor):
    
    def preprocess_cell(
        self,
        cell: NotebookNode,
        resources: Dict,
        index: int
    ) -> OutputPreprocessor:
        if _is_cell_markdown(cell) and "abstract" in _cell_tags_norm(cell):
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
        for c, unique in cell["metadata"].get("label", {}).items():
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
            resources.setdefault("labels", {}).setdefault(c, {})[unique] = number
        return cell, resources
    

RX_REFERENCE = re.compile(
    r"\^\[(?P<text>.*?)\]\((?P<counter>[a-z]+):(?P<unique>[-_a-zA-Z0-9]+)\)"
)


def _ref2anchor(counter: str, unique: str) -> str:
    return f"{counter}-{unique}"


def _dereference(
    resources: Dict,
    x: Union[NotebookNode, Tuple[str, str]],
    default: str = "??"
) -> str:
    if isinstance(x, NotebookNode):
        counter, unique = _get_label0(cast(NotebookNode, x))
    elif hasattr(x, "__iter__") and hasattr(x, "__len__") and len(x) == 2:
        counter, unique = x
    else:
        raise ValueError(f"Unsuitable reference holder: {repr(x)}")
        
    return resources.get("labels", {}).get(counter, {}).get(unique, default)


class SolverReferences(Preprocessor):
    
    def preprocess_cell(
        self,
        cell: NotebookNode,
        resources: Dict,
        index: int
    ) -> OutputPreprocessor:
        def solve(m: re.Match) -> str:
            template_ = m["text"].strip() or REFERABLE.get(
                m["counter"], {}
            ).get("ref", {})
            if isinstance(template_, dict):
                template = template_.get(resources.get("language", "en"), "")
            else:
                template = cast(str, template_ or "")
            if not template:
                log.error(
                    f"No template string provided for reference `{m.group(0)}' in cell "
                    f"{index}, and the counter `{m['counter']}' and language "
                    f"`{resources.get('language', 'en')}' do not suggest a "
                    "default template; will simply put out the number"
                )
                template = "{}"
            number = _dereference(resources, (m["counter"], m["unique"]), "")
            if not number:
                log.error(f"Reference label `{m['counter']}:{m['unique']}' is unbound.")
                number = "??"
            return (
                f'[{template.format(number)}](#{_ref2anchor(m["counter"], m["unique"])})'
            )
        
        if _is_cell_markdown(cell):
            resolved = RX_REFERENCE.sub(solve, cell.source)
            cell = copy_cell(cell)
            cell["source"] = resolved

        return cell, resources


def _get_annotator(counter: str, scheme_annotator: str = "") -> Annotator:
    if not scheme_annotator:
        if counter in REFERABLE:
            scheme_annotator = REFERABLE[counter]["annotation"]
        else:
            log.error(
                f"The label counter `{counter}' is not associated to a known "
                "annotator routine; we default to no cell modification (no-op) "
            )

    try:
        name_module, name_annotator = scheme_annotator.split(":")
    except ValueError:
        raise ValueError(
            f"Annotator descriptor `{scheme_annotator}' does not follow the "
            "`module:function' convention."
        )

    if name_module == ".":
        assert __name__ != "__main__"
        module = sys.modules[__name__]
    else:
        module = import_module(name_module)
    return getattr(module, name_annotator)


def _get_label0(cell: NotebookNode) -> Tuple[str, str]:
    assert len(cell.metadata.label) > 0
    return [(c, u) for c, u in cell.metadata.label.items()][0]


class RendererAnnotations(Preprocessor):
    
    def preprocess(self, nb: NotebookNode, resources: Dict) -> OutputPreprocessor:
        nb_new = NotebookNode({k: deepcopy(v) for k, v in nb.items() if k != "cells"})
        nb_new["cells"] = []
        i = 0
        while i < len(nb.cells):
            cell = nb.cells[i]
            if _is_cell_markdown(cell) and "label" in cell.metadata and (
                len(cell.metadata.label) > 0
            ):
                counter, unique = _get_label0(cell)
                if len(cell.metadata.label) > 1:
                    log.error(
                        "The only annotation scheme supported is for a cell adorned "
                        f"with a single label. Cell {i} has {len(cell.metadata.label)} "
                        "labels. We annotate here only according to "
                        f"label `{counter}:{unique}'"
                    )
                cells_new, resources, delta = _get_annotator(
                    counter.strip(),
                    cell.metadata.get("annotator", "").strip()
                )(nb, resources, i)
                assert delta > 0
            else:
                cells_new = [cell]
                delta = 1
            nb_new.cells += cells_new
            i += delta
        return nb_new, resources

    
def _prepend_anchor(cell: NotebookNode) -> NotebookNode:
    cell_new = copy_cell(cell)
    text = "".join(cell.source)
    counter, unique = _get_label0(cell)
    cell_new["source"] = f'<a name="{_ref2anchor(counter, unique)}"></a>\n\n{text}'
    return cell_new

    
def cut(
    notebook: NotebookNode,
    resources: Dict,
    i: int
) -> Tuple[Sequence[NotebookNode], Dict, int]:
    cell = notebook.cells[i]
    assert _is_cell_markdown(cell) and len(cell.metadata.get("label", {})) == 1
    counter, unique = _get_label0(cell)
    resources.setdefault("cuts", []).append(
        {
            "anchor": _ref2anchor(counter, unique),
            "text": cell.source
        }
    )
    return [], resources, 1


def legend(
    notebook: NotebookNode,
    resources: Dict,
    i: int
) -> Tuple[Sequence[NotebookNode], Dict, int]:
    cell_current = notebook.cells[i]
    cell_new = _prepend_anchor(cell_current)
    cell_new.metadata.setdefault("tags", []).append("displayed")
    cells_new = [cell_new]
    i_legend = i + 1
    if i_legend < len(notebook.cells) and "legend" in _cell_tags_norm(
        notebook.cells[i_legend]
    ):
        counter, unique = _get_label0(cell_current)
        cell_legend = copy_cell(notebook.cells[i_legend])
        description = REFERABLE.get(counter, {}).get("ref", {}).get(
            resources.get("language", "en"),
            "{}"
        ).capitalize().format(_dereference(resources, (counter, unique)))
        cell_legend["source"] = f"{description} &mdash; {''.join(cell_legend['source'])}"
        cells_new.append(cell_legend)
        
    return cells_new, resources, len(cells_new)


def margin(
    notebook: NotebookNode,
    resources: Dict,
    i: int
) -> Tuple[Sequence[NotebookNode], Dict, int]:
    cell = copy_cell(notebook.cells[i])
    number = _dereference(resources, cell)
    text = "".join(cell.source)
    cell["source"] = (
        f'<div class="annotated-main">{text}</div>'
        f'<div class="annotation-margin">({number})</div>'
    )
    return [_prepend_anchor(cell)], resources, 1


def number(
    notebook: NotebookNode,
    resources: Dict,
    i: int
) -> Tuple[Sequence[NotebookNode], Dict, int]:
    cell = copy_cell(notebook.cells[i])
    counter, unique = _get_label0(cell)
    number = _dereference(resources, cell)
    text = "".join(cell.source).strip()
    token, rest = text.split(maxsplit=1)
    cell["source"] = (
        f'{token} <a name="{_ref2anchor(counter, unique)}"></a>{number}. {rest}'
    )
    return [cell], resources, 1


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
