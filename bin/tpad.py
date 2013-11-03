#!/usr/bin/python


from oauth.oauth import OAuthConsumer, OAuthToken
import difflib
import marshal
import optparse
import os.path
import pygdown
import sys
import typepad
import BaseHTTPServer


_APP = '6p019b0091d4cf970b'
_CONSUMER_KEY = '259a01afff0dfc74'
_ACCESS_CACHE = '.blog.token'
_BLOG_ID = '6a019b00807617970d019b00800d4e970c'


class Post(object):

  def __init__(self, blog, asset):
    self.blog = blog
    self.asset = asset

  def get_source_name(self):
    title = self.asset.title
    title_part = title.lower().replace(' ', '-')
    published = self.asset.published
    date_part = published.strftime('%Y-%m-%d')
    return '%s-%s.md' % (date_part, title_part)

  def get_contents(self):
    return self.asset.content

  def set_contents(self, value):
    self.asset.content = value
    self.asset.text_format = 'html'
    return self.asset.put()


# Encapsulates access to the blog.
class BlogAccess(object):

  def __init__(self, url_id, consumer_key, consumer_secret):
    self.blog = None
    self.url_id = url_id
    self.consumer_key = consumer_key
    self.consumer_secret = consumer_secret
    self.authenticated = False

  # Tries to authenticate access to the user, either interactively or using
  # cached credentials.
  def ensure_authenticated(self):
    if self.authenticated:
      return
    self.authenticated = True
    consumer = OAuthConsumer(self.consumer_key, self.consumer_secret)
    if os.path.exists(_ACCESS_CACHE):
      access_data = marshal.load(open(_ACCESS_CACHE, 'r'))
      access_token = OAuthToken(access_data['key'], access_data['secret'])
      typepad.client.add_credentials(consumer, access_token, domain='api.typepad.com')
    else:
      app = typepad.Application.get_by_id(_APP)
      access_token = typepad.client.interactive_authorize(consumer, app)
      access_data = {'key': access_token.key, 'secret': access_token.secret}
      marshal.dump(access_data, open(_ACCESS_CACHE, 'w'))

  # Returns the blog this object provides access to.
  def get_blog(self):
    if self.blog is None:
      self.ensure_authenticated()
      self.blog = typepad.api.Blog.get_by_url_id(self.url_id)
    return self.blog

  # Returns a list of all the posts on this blog.
  def get_posts(self):
    return [Post(self.blog, asset) for asset in self.get_blog().post_assets]

  # Returns the post generated from a markdown source file with the given name.
  # If none could be found None is returned.
  def get_post_for_source_name(self, source_name):
    for post in self.get_posts():
      if post.get_source_name() == source_name:
        return post


_SECRET_ENV_NAME = 'TPAD_CONSUMER_SECRET'
_PREVIEW_TEMPLATE = """
<html xmlns="http://www.w3.org/1999/xhtml" id="typepad-standard">
  <head>
    <link rel="stylesheet" href="http://blog.ne.utrino.org/styles.css?v=6" type="text/css" media="screen" />
  </head>
  <body>
    <div id="container">
      <div id="container-inner" class="pkg">
        <div id="banner">
          <div id="banner-inner" class="pkg">
            <h1 id="banner-header">
              <a href="...">Neutrino Language Blog</a>
            </h1>
            <h2 id="banner-description">
              all about the neutrino programming language
            </h2>
         </div>
        </div>
        <div id="nav">
          <ul class="nav-list pkg">
            <li class="nav-list-item"><a href="http://neutrino.typepad.com/blog/">Home</a></li>
            <li class="nav-list-item"><a href="http://neutrino.typepad.com/blog/archives.html">Archives</a></li>
            <li class="nav-list-item"><a href="http://profile.typepad.com/6p019b00807617970d">Profile</a></li>
            <li class="last-nav-list-item nav-list-item"><a href="http://neutrino.typepad.com/blog/atom.xml">Subscribe</a></li>
          </ul>
        </div>
      </div>
      <div id="pagebody">
        <div id="pagebody-inner" class="pkg">
          <div id="alpha">
            <div id="alpha-inner" class="pkg">
              <div class="entry-type-post entry">
                <div class="entry-content">
                  <div class="entry-body">
%s
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>
"""


# Takes the appropriate action based on the command issued.
class Dispatcher(object):

  def __init__(self, flags, env):
    self.flags = flags
    self.env = env

  def dispatch(self, args):
    command = args[0]
    try:
      handler = getattr(self, 'handle_%s' % command)
    except AttributeError, e:
      raise Exception('Unknown command "%s".' % command)
    (handler)(*args[1:])

  # Updates the given post on typepad.
  def handle_update(self, filename):
    consumer_secret = self.env[_SECRET_ENV_NAME]

    # Generate the new contents.
    source_name = os.path.basename(filename)
    source = open(filename, 'rt').read()
    new_post_html = self.convert(source)

    # Read the existing contents.
    access = BlogAccess(_BLOG_ID, _CONSUMER_KEY, consumer_secret)
    post = access.get_post_for_source_name(source_name)
    if post is None:
      raise Exception('Found no post that matched %s' % source_name)
    old_post_html = post.get_contents()

    # Ask for confirmation
    new_post_lines = new_post_html.splitlines()
    old_post_lines = old_post_html.splitlines()
    diff = list(difflib.unified_diff(old_post_lines, new_post_lines))
    if len(diff) == 0:
      print "The live post is up to date."
    else:
      print "About to make the following changes:"
      for line in diff:
        print line
      proceed = raw_input("Proceed? [yN]: ")
      if proceed.lower() == 'y':
        post.set_contents(new_post_html)

  def convert(self, source):
    return pygdown.convert(source).replace('\'', '&#39;')

  def handle_edit(self, filename):
    outer = self
    class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
      def do_GET(self):
        outer.convert_and_serve(filename, self)
      def log_request(self, *whatever):
        # How about a nice cup of shut the fuck up?
        pass
    server_address = ('', 8000)
    httpd = BaseHTTPServer.HTTPServer(server_address, Handler)
    httpd.serve_forever()

  def convert_and_serve(self, filename, request):
    handle = open(filename, 'rt')
    contents = handle.read()
    handle.close()
    html = pygdown.convert(contents)
    request.send_response(200)
    request.send_header("Content-type", "text/html")
    request.end_headers()
    request.wfile.write(_PREVIEW_TEMPLATE % html)
    request.wfile.close()

# Parse command-line options and validate the state of the environment.
def parse_options(args):
  env = os.environ
  if not _SECRET_ENV_NAME in env:
    raise Exception('Environment variable %s should be set' % _SECRET_ENV_NAME)
  return ({}, args, env)


def main():
  (flags, args, env) = parse_options(sys.argv[1:])
  Dispatcher(flags, env).dispatch(args)


if __name__ == '__main__':
  main()
