import markdown
from jinja2 import Template

class HTMLRenderer:
    """MARP Markdown을 HTML로 변환하여 미리보기 지원"""

    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Presentation Preview</title>
        <link rel="stylesheet" href="https://unpkg.com/marpit@latest/marpit.min.css">
    </head>
    <body>
        <div class="marpit">
            {{ content | safe }}
        </div>
    </body>
    </html>
    """

    @staticmethod
    def render(md_content: str) -> str:
        """Markdown을 HTML로 변환하여 미리보기 제공"""
        html_content = markdown.markdown(md_content, extensions=["extra", "toc", "sane_lists"])
        template = Template(HTMLRenderer.HTML_TEMPLATE)
        return template.render(content=html_content)
