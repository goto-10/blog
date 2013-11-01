# Converts markdown with pygments enclosed in [source:<language>]...[/source]
# to html.

import markdown
import markdown.preprocessors
import optparse
import pygments.formatters
import pygments.lexers
import pygtrino
import re
import sys


_CODE_CLASS = 'codehilite'
_SOURCE_BLOCK_PATTERN = re.compile(r'\[source:(\w*)\](.*)\[/source\]', re.S)
_BLOCK_OUTPUT_TEMPLATE = '\n\n<div class="%s">%%s</div>\n\n' % _CODE_CLASS


# Parses command-line flags.
def parse_flags(args):
  parser = optparse.OptionParser()
  parser.add_option('-i', '--in', dest='_in')
  return parser.parse_args(args)


def get_lexer_by_name(name):
  if name == 'neutrino':
    return pygtrino.NeutrinoLexer()
  else:
    return pygments.lexers.get_lexer_by_name(name)


# Converts any [source] blocks to html using pygments.
def convert_pygments(source):
  # Replaces an individual source block to html.
  def replace(match):
    language = match.group(1)
    code = match.group(2)
    lexer = get_lexer_by_name(language)
    formatter = pygments.formatters.HtmlFormatter(cssclass='hll', linenos='inline')
    highlighted = pygments.highlight(code, lexer, formatter)
    return _BLOCK_OUTPUT_TEMPLATE % highlighted
  return _SOURCE_BLOCK_PATTERN.sub(replace, source)


# Convertes markdown to html.
def convert_markdown(source):
  return markdown.Markdown().convert(source)


# Does the whole conversion process.
def process(input=None):
  source = open(input, "rt").read()
  pygmented = convert_pygments(source)
  markdowned = convert_markdown(pygmented)
  print markdowned


# Main entry-point.
def main():
  (flags, args) = parse_flags(sys.argv)
  process(input=flags._in)


if __name__ == '__main__':
  main()
