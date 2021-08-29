import pypandoc

from src.converters.converter import *
from src.logger import Logger


class DocumentConverter(Converter):
    """
    Document Converter class used for converting documents in defined formats
    Conversion can be done from specified input (AVAILABLE_INPUT_FORMATS)
    to output (AVAILABLE_OUTPUT_FORMATS) file formats
    Depends on latex engine (Requires TeXlive)
    """
    AVAILABLE_INPUT_FORMATS = [
        'bibtex', 'biblatex', 'commonmark', 'commonmark_x', 'creole', 'csljson', 'csv', 'docbook', 'docx', 'dokuwiki',
        'epub', 'fb2', 'gfm', 'haddock', 'html', 'ipynb', 'jats', 'jira', 'json', 'latex', 'markdown', 'markdown_mmd',
        'markdown_phpextra', 'markdown_strict', 'mediawiki', 'man', 'muse', 'native', 'odt', 'opml', 'org', 'rtf',
        'rst', 't2t', 'textile', 'tikiwiki', 'twiki', 'vimwiki'
    ]
    AVAILABLE_OUTPUT_FORMATS = [
        'asciidoc', 'beamer', 'bibtex', 'biblatex', 'commonmark', 'commonmark_x', 'context', 'csljson', 'docbook',
        'docbook5', 'docx', 'dokuwiki', 'epub', 'epub2', 'fb2', 'gfm', 'haddock', 'html', 'html4', 'icml', 'ipynb',
        'jats_archiving', 'jats_articleauthoring', 'jats_publishing', 'jats', 'jira', 'json', 'latex', 'man',
        'markdown', 'markdown_mmd', 'markdown_phpextra', 'markdown_strict', 'mediawiki', 'ms', 'muse', 'native', 'odt',
        'opml', 'opendocument', 'org', 'pdf', 'plain', 'pptx', 'rst', 'rtf', 'texinfo', 'textile', 'slideous', 'slidy',
        'dzslides', 'revealjs', 's5', 'tei', 'xwiki', 'zimwiki']

    def __init__(self):
        super().__init__()
        self.logger = Logger("doc_conv")

    def convert(self, document_path, new_format):
        """
        Converts document to a specified format
        In process creates temporary file (unavoidable using pypandoc)
        Returns filepath of temporary file
        :param document_path: str
        :param new_format: str
        :return: str
        :raises: UnsupportedFormatException
        """
        self.logger.debug(f"Converting document from at {document_path} to {new_format}")

        if new_format not in self.AVAILABLE_OUTPUT_FORMATS:
            error_message = f"Format {new_format} is not supported to convert to"
            self.logger.error(error_message)
            raise UnsupportedFormatException(error_message)
        old_format = document_path.split(".")[-1]
        if old_format not in self.AVAILABLE_INPUT_FORMATS:
            error_message = f"Format {old_format} is not supported to convert from"
            self.logger.error(error_message)
            raise UnsupportedFormatException(error_message)

        new_file_path = document_path.replace(old_format, new_format)

        try:

            pypandoc.convert_file(document_path, new_format, outputfile=new_file_path)

            self.logger.info(f"Converted document {document_path} to {new_file_path}")
            return new_file_path
        except RuntimeError as e:
            raise UnsupportedFormatException(e)
