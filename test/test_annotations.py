import json
from textwrap import dedent
from traitlets.config import Config
from typing import *

from . import export_notebook


def run_test(
    name_nb: str,
    expected_cells: List[str],
    expected_cuts: List[Dict[str, str]]
) -> None:
    c = Config()
    c.Exporter.preprocessors = [
        "nbconvert_article_html.CollectorLabels",
        "nbconvert_article_html.RendererAnnotations"
    ]
    c.CollectorLanguage.enabled = True
    c.CollectorLabels.enabled = True
    c.RendererAnnotations.enabled = True
    nb_, resources = export_notebook(name_nb + ".ipynb", c)
    nb = json.loads(nb_)
    assert expected_cells == [''.join(cell["source"]) for cell in nb["cells"]]
    if expected_cuts:
        assert "cuts" in resources
        assert resources["cuts"] == expected_cuts


def test_annotations_common():
    run_test(
        "annotations-common",
        [
            '# <a name="sec-one"></a>1. Section one',
            '# <a name="sec-major"></a>2. Other major division',
            "Let's not forget^[](note:forgetting) our families here.",
            dedent("""\
                <a name="tab-mind"></a>

                |Keep in mind|
                |------------|
                |Families    |
                |Look up what forgetting is|\
            """.rstrip()),
            "Table 1 &mdash; The things to keep in mind.",
            '## <a name="sec-minor"></a>2.1. And first minor division',
            dedent("""\
                <a name="fig-code"></a>

                ```python
                def f(a, b):
                    print(a + b)
                ```\
            """.rstrip()),
            "Figure 1 &mdash; This is the code of function `f`.",
            (
                '<a name="eq-a-plus-b"></a>\n\n'
                '<div class="annotation-container">'
                '<div class="annotated-main">$$f(a, b) = a + b$$</div>'
                '<div class="annotation-margin">(1)</div>'
                '</div>'
            )
        ],
        [
            {
                "note": "1",
                "anchor": "note-forgetting",
                "text": "Forgetting is what again?"
            }
        ]
    )
