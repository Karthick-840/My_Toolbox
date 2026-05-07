from IPython.display import Markdown
import textwrap

def to_markdown(text):
    # Replace periods with asterisks
    text = text.replace('.', '*')
    indented_text = textwrap.indent(text, '>', predicate=lambda line: True)
    return Markdown(indented_text)