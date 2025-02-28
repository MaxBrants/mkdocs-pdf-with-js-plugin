
from mkdocs.config import config_options
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page
from jinja2 import Template


from pdf_with_js.printer import Printer


class PdfWithJS(BasePlugin):

    config_scheme = (
        ('enable', config_options.Type(bool, default=True)),
        ('coverTemplate', config_options.Type(str, default=""))
    )

    def __init__(self):

        self.printer = Printer()
        self.cover_template = ""
        pass

    def on_config(self, config, **kwargs):
        self.enabled = self.config['enable']
        return config

    def on_nav(self, nav, config, files):
        return nav
    
    def on_page_context(self, context, page, config, nav):
        
        cover_template = Template(self.config['coverTemplate'])
        self.cover_template = cover_template.render(context)

        return context

    def on_post_page(self, output_content, page, config, **kwargs):
        if not self.enabled:
            return output_content

        page_paths = self.printer.add_page(page, config)
        output_content = self.printer.add_download_link(output_content, page_paths)

        output_content = self.printer.add_Cover_Page(output_content, self.cover_template)

        return output_content

    def on_post_build(self, config):
        if not self.enabled:
            return

        self.printer.print_pages()
