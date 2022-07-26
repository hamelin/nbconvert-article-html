import json
from traitlets.config import Config
from typing import *

from . import export_notebook


def run_test(name_nb: str, expected: Dict[int, str]) -> None:
    c = Config()
    c.Exporter.preprocessors = [
        "nbconvert_article_html.CollectorLanguage",
        "nbconvert_article_html.CollectorLabels",
        "nbconvert_article_html.SolverReferences"
    ]
    c.CollectorLanguage.enabled = True
    c.CollectorLabels.enabled = True
    c.SolverReferences.enabled = True
    nb_, _ = export_notebook(name_nb + ".ipynb", c)
    nb = json.loads(nb_)
    for i, source_expected in expected.items():
        assert source_expected == "".join(nb["cells"][i]["source"])


def test_references_simple():
    run_test(
        "references-simple",
        {
            4: (
                "In reverse order, I can reference equations [2](#eq-exponential) and "
                "[1](#eq-quadratic)."
            )
        }
    )


def test_references_custom():
    run_test(
        "references-custom",
        {
            2: (
                "From here, I can reference Section [1](#sec-one) using the default "
                "reference, as well as put [my own link, 2](#sec-two)."
            )
        }
    )


def test_references_before_appearance():
    run_test(
        "references-before-appearance",
        {
            0: (
                "La magie de la séquence de préprocesseurs fait en sorte que je peux "
                "référer à la [figure 1](#fig-quadratic) avant qu'elle n'apparaisse "
                "dans le texte."
            )
        }
    )


def test_references_notes():
    run_test(
        "references-notes",
        {
            0: (
                "From here, I want to set aside a "
                "note.[<sup>1</sup>](#note-link-external)"
            )
        }
    )
