from traitlets.config import Config
from typing import *

from . import export_notebook


def run_test(name_nb: str) -> Dict:
    c = Config()
    c.Exporter.preprocessors = ["nbconvert_article_html.CollectorLabels"]
    c.CollectorLabels.enabled = True
    return export_notebook(name_nb + ".ipynb", c)[1]


def test_labels_normal():
    resources = run_test("labels_non_hierarchical")
    assert "labels" in resources
    assert resources["labels"] == {
        "note": {"a-note": "1"},
        "eq": {"quadratic": "1", "derivative": "2"},
        "fig": {"some-code": "1"},
        "tab": {"head-foot": "1"}
    }


def test_labels_hierarchical():
    resources = run_test("labels_hierarchical")
    assert {
        "sec": {
            "toplevel": "1",
            "level2": "1.1",
            "level3": "1.1.1",
            "other3": "1.1.2",
            "one-more": "1.1.3",
            "at2now": "1.2",
            "reset3": "1.2.1",
            "further3": "1.2.2",
            "backto1": "2",
            "ready21": "2.1",
            "skip": "2.2",
            "and-into": "2.2.1",
            "final": "2.2.2"
        }
    } == resources["labels"]
