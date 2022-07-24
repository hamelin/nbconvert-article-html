from textwrap import dedent
from typing import *

from traitlets.config import Config

from . import export_notebook


def run_test(name_nb: str, expected: Optional[str]) -> Dict:
    c = Config()
    c.TemplateExporter.preprocessors = ["nbconvert_article_html.CollectorAbstract"]
    c.CollectorLabels.enabled = True
    _, resources = export_notebook(name_nb + ".ipynb", c)
    if expected is None:
        assert "abstract" not in resources
    else:
        assert "abstract" in resources
        assert isinstance(resources["abstract"], list)
        assert dedent(expected.rstrip()) == "\n\n".join(resources["abstract"])


def test_no_abstract():
    run_test("no-abstract", None)


def test_abstract_one_cell():
    run_test(
        "abstract-one-cell",
        """\
        This _is_ the abstract.
        
        There is more than one paragraph to it.\
        """
    )


def test_abstract_one_cell_single_string():
    run_test(
        "abstract-one-cell-single-string",
        """\
        This _is_ the abstract.
        
        There is more than one paragraph to it.\
        """
    )
    
    
def test_abstract_three_cells():
    run_test(
        "abstract-three-cells",
        """\
        This _is_ the abstract.
        
        There is more than one paragraph to it.
        
        This, though, is also in the abstract.
        
        And, finally, this.\
        """
    )
