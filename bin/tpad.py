#!/usr/bin/python


from oauth.oauth import OAuthConsumer, OAuthToken
import difflib
import marshal
import optparse
import os.path
import pygdown
import sys
import typepad


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
    self.asset.contents = value
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
      access_data = marshal.load(open(_ACCESS_CACHE, "r"))
      access_token = OAuthToken(access_data['key'], access_data['secret'])
      typepad.client.add_credentials(consumer, access_token, domain='api.typepad.com')
    else:
      app = typepad.Application.get_by_id(_APP)
      access_token = typepad.client.interactive_authorize(consumer, app)
      access_data = {'key': access_token.key, 'secret': access_token.secret}
      marshal.dump(access_data, open(_ACCESS_CACHE, "w"))

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


# Parse command-line options and validate the state of the environment.
def parse_options(args):
  env = os.environ
  if not _SECRET_ENV_NAME in env:
    raise Exception('Environment variable %s should be set' % _SECRET_ENV_NAME)
  return ({}, args, env)


def main():
  (flags, args, env) = parse_options(sys.argv[1:])
  consumer_secret = env[_SECRET_ENV_NAME]

  # Generate the new contents.
  source_path = args[0]
  source_name = os.path.basename(source_path)
  source = open(source_path, "rt").read()
  new_post_html = pygdown.convert(source)

  # Read the existing contents.
  access = BlogAccess(_BLOG_ID, _CONSUMER_KEY, consumer_secret)
  post = access.get_post_for_source_name(source_name)
  if post is None:
    raise Exception('Found no post that matched %s' % source_name)
  old_post_html = post.get_contents()

  # Ask for confirmation
  new_post_lines = new_post_html.splitlines()
  old_post_lines = old_post_html.splitlines()
  diff = list(difflib.unified_diff(new_post_lines, old_post_lines))
  if len(diff) == 0:
    print "The live post is up to date."
  else:
    print "About to make the following changes:"
    for line in diff:
      print line
    proceed = raw_input("Proceed? [yN]: ")
    if proceed.lower() == 'y':
      post.set_contents(new_post_html)


if __name__ == '__main__':
  main()
