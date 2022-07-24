from pathlib import Path
from typing import *

from nbconvert.exporters import HTMLExporter
from nbconvert.preprocessors import Preprocessor
from nbformat import NotebookNode


# class ArticleHTML(HTMLExporter):


OutputPreprocessor = Tuple[NotebookNode, Dict]


class CollectorNotes(Preprocessor):
    
    def preprocess_cell(
        self,
        cell: NotebookNode,
        resources: Dict,
        index: int
    ) -> OutputPreprocessor:
        return cell, resources


class CollectorLabels(Preprocessor):
    
    def preprocess_cell(
        self,
        cell: NotebookNode,
        resources: Dict,
        index: int
    ) -> OutputPreprocessor:
        return cell, resources
    
    
class SolverRefs(Preprocessor):
    
    def preprocess_cell(
        self,
        cell: NotebookNode,
        resources: Dict,
        index: int
    ) -> OutputPreprocessor:
        return cell, resources

    
class NumbererHeadings(Preprocessor):
    
    def preprocess_cell(
        self,
        cell: NotebookNode,
        resources: Dict,
        index: int
    ) -> OutputPreprocessor:
        return cell, resources

    
class AnnotatorLegends(Preprocessor):
    
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
