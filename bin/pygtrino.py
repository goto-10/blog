from pygments.lexer import RegexLexer, bygroups
from pygments.token import *


# See http://pygments.org/docs/lexerdevelopment/ for background.
ROOT_TOKENS = [
  (r'\"[^\"]*\"',                      Literal.String),
  (r'##.*\n',                          Comment),
  (r'#.*\n',                           Comment.Single),
  (r'[$]+([A-Za-z][A-Za-z0-9_:]*)?',   Name.Variable),
  (r'[@]+([A-Za-z][A-Za-z0-9_:]*)?',   Name.Class),
  (r'[A-Za-z0-9_]+:',                  Name.Tag),
  (r'(\.)([A-Za-z][A-Za-z0-9_]*)',     bygroups(Text, Name.Function)),
  (r'(:=|=>)',                         Punctuation),
  (r'(\.?)([!+=<>/*%-]+)',             bygroups(Text, Operator)),
  (r'\b(true|false|null)\b',           Keyword.Constant),
  (r'\b(type|def|var|import)\b',       Keyword.Declaration),
  (r'\b[A-Za-z][A-Za-z0-9_]+\b',       Keyword),
  (r'[0-9]+',                          Number),
  (r'.',                               Text)
]


class NeutrinoLexer(RegexLexer):
  name = 'Neutrino'
  aliases = ['neutrino']
  filenames = ['*.n']
  tokens = {'root': ROOT_TOKENS}
