# Article-HTML exporter and template for nbconvert

This package provides an exporter and template to render a Jupyter notebook into a self-contained HTML file whose layout is similar to a LaTeX article.
Such documents are presented so as to facilitate their reading and perusal both on a print-out and a screen,
all in an economical text format whose low-level inspection and repair is easy.
See an [example](examples/Demonstration%20EN.html) to get the gist.

## Installing

From PyPI:

```sh
pip install nbconvert-article-html
```

## Usage

The simplest way to use this package is to invoke nbconvert from the command line:

```bash
jupyter nbconvert --to article-html my-notebook.ipynb
```

As is [well known](https://nbconvert.readthedocs.io/en/latest/nbconvert_library.html), one may also run this from Python code:

```python
from nbconvert_article_html import ArticleHTMLExporter

exporter = ArticleHTMLExporter()
html, resources = exporter.from_filename("examples/Demonstration FR.html")
```

## Writing the source notebook

The source document for the final article is a single Jupyter notebook, mainly composed of Markdown cells, as well as the odd code cells.
The exporter and template make heavy use of notebook and cell metadata.
If anything below feels unclear, please take a look at either the demonstration notebook in [English](examples/Demonstration%20EN.html) or [French](examples/Demonstration%20FR.html).

### Language, title, authors and date

Four fields of the metadata of the notebook get rendered into a header for the final document:

`language`

> The [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) two-letter code for the language in which the notebook is written.
> This is used to internationalize the rendering of the final article, so that the abstract's heading is rendered as *Abstract* in English, *Résumé* in French, and so on.
> So far, only languages `en` and `fr` are supported.

`title`

> The title of the document.

`authors`

> The list of authors of the document.
> To make way for future versions of this notebook that may leverage further information about authors,
> each author in the list should be written up as an object, with at least a `name` field indicating their name.

`date`

> The date used to timestamp the document just below the author list.
> Any string can be used here.
> If no date is provided, the current day's date is used, formatted like `yyyy-mm-dd`.

### Abstract

The document can be given a short abstract.
It is written up in cells given the tag `abstract`.
These tagged cells are taken out of the document's body and rendered at the top of the document, just below its opening header.

### Labels and references

This exporter and template favor an authoring style where each paragraph and "spacy" component of the document is written in its own cell.
This facilitates the labeling and referencing of every component.

The LaTeX typesetting system has set the standard for internal references, through its `\label` and `\ref` constructs.
We take inspiration from these constructs, leveraging the features of the Jupyter notebook used as a source document.
The way a `\label` numbers artifacts in context in a LaTeX file,
`article-html` labels specific notebook cells.
To do so, one adds a `label` metadata field to a cell to mark,
associated to an object that indicates the marking context and unique name to give it.

Anywhere in the document, a labeled component can be referenced using a small extension to the Markdown syntax.
Assuming that the component was marked in context `ctx` and was given the unique name `name`,
one refers to this component with the construct

```
^[](ctx:name)
```

This will render a context-specific link to an internal [HTML anchor](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/a) associated to the component that will include the number.
To determine the text of this link, one can write

```
^[component no {}](ctx:name)
```

The `{}` placeholder will be substituted with the number associated to the component.
The following details the components whose labeling was implemented, and the conventions that facilitate the best rendering of their automatic numbering.

#### Headings

The system assumes that a heading cell starts with a heading line (e.g. `# Heading`).
It is labeled by adding the following to the metadata:

```json
"label": {"sec": "unique-name"}
```

Such a labeled heading cell can then be refered to with the syntax `^[](sec:unique-name)`.
It will then be rendered in HTML as

```html
<a name="sec-unique-name"></a>

<h#>[NUMBER]. Heading</h#>
```

Headings are numbered hierarchically, with each sub-heading number being prepended with the parent section's number, separated with a dot.
Only labeled headings are numbered.
If one omits labeling a certain heading, it is rendered unnumbered, and the next labeled one continues the sequence.

#### Notes

It is perhaps poor writing style, but I use footnotes a lot.
In HTML, one does not have pages, so footnotes become end notes, and all go at the end of the document.
This is also the preferred place for an author to document their references.
This stands in contrast to the inline referencing style of hyperlinked documents, whose reading is typically intended to be online and on-screen.
This template preconises rather the classic approach of documenting references with end notes, even with hyperlinks written up explicitly.
This effectively enables the offline reader to follow up on the references when they go online eventually.

The document's end notes are authored on the fly, amongst the text of the document.
They are identified by labeling them thus:

```json
"label": {"note": "unique-name"}
```

The text of the note is extracted during the exportation process, and rendered in a list at the end of the document.
Each note is associated to an anchor named `note-unique-name`.
One refers to such a note using the construct `^[](note:unique-name)`.
By default, the reference is rendered as the hyperlinked note number, in exponent.

#### Equations

Jupyter notebooks already make mathematics typesetting availabel when they are authored using [MathJax](https://www.mathjax.org/).
This extension to HTML 5 is provided also in exported HTML, and `article-html` adds automatic numbering of labeled expressions.
It is assumed that any cell labeled as mathematics contains only one expression, typeset in *display mode* (e.g. `$$<equation>$$`).

```json
"label": {"eq": "unique-name"}
```

Similarly as for headings and notes, one refers to a labeled equation with the notation `^[](eq:unique-name)` .
As in LaTeX, the numbered displayed equations are rendered with their equation number on the right margin of the document, between parentheses.
The equation is prepended with an anchor named `eq-unique-name`.

#### Figures and tables

This template enables the rendering of images and tabular data anywhere, inline if one must.
However, it is so convenient to be able to refer to a figure or table, and have a *legend* (a [*caption*](https://en.wikibooks.org/wiki/LaTeX/Floats,_Figures_and_Captions#Captions) in LaTeX lingo) underneath explaining what's going on there.

Any cell can be labeled as being a figure or a table, using the following alternative notations:

```json
"label": {"fig": "unique-name"}
"label": {"tab": "unique-name"}
```

The cell that follows the labeled one is expected to be its legend:
a short paragraph describing the figure or table.
To be recognized as the legend, the author must add `legend` to that cell's tags.
The legend cell will be rendered with either prefix `Figure {} &mdash;` or `Table {} &mdash;`,
with the placeholder `{}` substituted with the number of the figure or table.
Both the figure and its legend also have some styling associated to make centered in the reading area, and put some emphasis on it.
It is also prepended with an anchor named either `fig-unique-name` or `tab-unique-name`.
Regardless of whether a legend is provided, one refers to tables and images using the notations `^[](fig:unique-name)` or `^[](tab:unique-name)`.

### Excluding cells

When authoring a document through a notebook, one would sometimes choose to drop some material from the document, or to add comments *in petto*.
I personally find it very useful to use `---` in cells here and there to visualize the sections of a notebook better,
but I would not want these horizontal rules to be present in my final document.
To exclude a cell from the rendering, one can add `drop` to its tags.

## Customization

The system is implemented as a thin wrapper around nbconvert's stock [`HTMLExporter`](https://github.com/jupyter/nbconvert/blob/3b21cba86c4cadc2bdabb237219d23a32be22f70/nbconvert/exporters/html.py), coupled with several preprocessors and a custom template.
These preprocessors don't offer anything in terms of customization yet, but one may easily tailor the styling of the document by extending the template named `article-html`.

For instance, let's have a custom template named **article-airy** that adds more space between the abstract and the rest of the article. In one of the directories listed under `data:` when running `jupyter --paths`, add the directory `article-airy`. In that directory, add these file:

`.../article-airy/conf.json`:

```json
{
    "base_template": "article-html",
    "mimetypes": {"text/html": true}
}
```

`.../article-airy/index.html.j2`:

```jinja2
{% extends 'article-html/index.html.j2' %}

{%- block notebook_css -%}
{{ super() }}
<style type="text/css">
div.abstract {
    margin-bottom: 1.5in;
}
</style>
{%- endblock notebook_css -%}
```


## Development

### Setup

My favored development environment uses Conda.
Git-clone the project, then run

```sh
conda env create
conda activate nbconvert-article-html
```

### Code quality checks

I use [Flake8](https://github.com/pycqa/flake8) and type annotations ([mypy](http://mypy-lang.org/)) to track code issues statically,
as well unit tests (run with [pytest](https://docs.pytest.org/en/7.1.x/)) to ensure some baseline code properties.
One day I'll write up a script to run all these elegantly, but until then, I use this command line:

```
mypy --ignore-missing-imports . && pytest && flake8
```

### Organization

As suggested [here](https://nbconvert.readthedocs.io/en/latest/external_exporters.html#writing-a-custom-exporter), I have rolled my extensive custom package into a custom nbconvert exporter.
This turned out to be more than just a packaging trick, as late in development I discovered I needed to tweak some code-based functionality of the `HTMLExporter` base class.
However, pretty much all features of this package are driven by a sequence of notebook preprocessors configured through the [`conf.json`](nbconvert_article_html/template/article-html/conf.json) core template file.

#### Intended exportation workflow

The usage of a sequence of preprocessing steps facilitates the reading of the code:
the intents pursued are not all tangled in one long and messy preprocessor.
Here is the sequence of preprocessors and how we intend they respectively transform the input notebook prior to HTML rendering.
Remark that the sequence of preprocessors all share a free-form dictionary called `resources`, which enables passing data between them.

1. `CollectorLanguage`: picks up the language of the notebook and initializes resources with proper string translations.
1. `CollectorLabels`: maps into the resource dictionary the cell labels to their computed numbers.
1. `SolverReferences`: replaces all instances of the `^[...](...)` notation in the Markdown cells with proper Markdown internal links to the appropriate anchors.
1. `RendererAnnotations`: visits labeled cells and changes their text in order to incorporate the number of the component in a specific manner.
1. `CollectorAbstract`: captures the text of the abstract into .
1. We then configure the standard by-tag cell removal preprocessor so that it discards cells tagged `drop` or `abstract`.

The exportation then proceeds with a core HTML template that replaces a lot of Jupyter's own styling material
(which I find bloated and excessive).
This template provides the rendering of the header and the abstract prior to the document's own core, which is followed with a level-1 section of end notes.
