import functools
import os
import re
import uuid
from collections import OrderedDict, defaultdict
from itertools import islice

import markdown
import pymdownx.superfences
from django.apps import apps
from django.conf import settings
from django_hosts import reverse
from frontmatter import Post

from blog.apps import BlogConfig
from common.singleton import Singleton

app_config: BlogConfig = apps.get_app_config('blog')


class keydefaultdict(defaultdict):
    def __missing__(self, key):
        if not self.default_factory:
            raise KeyError(key)
        ret = self[key] = self.default_factory(key)
        return ret


class BlogSite(metaclass=Singleton):
    def __init__(self):
        self.posts = OrderedDict()
        self.categories = keydefaultdict(BlogCategory)
        self.tags = keydefaultdict(BlogTag)
        self.index = 0

    def __iter__(self):
        return self

    def __len__(self):
        paginate = app_config.paginate
        return len(self.posts) // paginate + int(bool(len(self.posts) % paginate))


    def __next__(self):
        paginate = app_config.paginate
        result = OrderedDict()
        for key, value in islice(reversed(self.posts.items()), paginate * self.index, paginate * (self.index + 1)):
            result[key] = value
        if not result:
            self.index = 0
            raise StopIteration
        self.index += 1
        paginate_page = BlogPaginatePage(self.index, result)
        # 非第一页
        if self.index > 1:
            paginate_page.previous_page = '{}.html'.format(self.index - 1)
        # 非最后一页
        if self.index * paginate < len(self.posts):
            paginate_page.next_page = '{}.html'.format(self.index + 1)
        return paginate_page

    def add_post(self, post):
        try:
            previous = next(reversed(self.posts.values()))
            previous.next = post
            post.previous = previous
        except StopIteration:
            pass
        self.posts[post.name] = post
        # 分类归类
        for category_name in post.categories:
            self.categories[category_name].posts[post.name] = post
        # 标签归类
        for tag_name in post.tags:
            self.tags[tag_name].posts[post.name] = post

    @functools.lru_cache()
    def to_dict(self):
        return app_config.to_dict()


class BlogPaginatePage(object):
    def __init__(self, current, posts, previous_page=None, next_page=None):
        self.current = current
        self.posts = posts
        self.previous_page = previous_page
        self.next_page = next_page

    def __repr__(self):
        return 'current: {}, previous_page: {}, next_page: {}'.format(self.current, self.previous_page, self.next_page)

    @property
    @functools.lru_cache()
    def url(self):
        if self.current == 1:
            return 'index.html'
        else:
            return '{}.html'.format(self.current)

    @functools.lru_cache()
    def to_dict(self):
        d = dict(
            posts=[post.to_dict() for post in self.posts.values()],
            previous_page=self.previous_page,
            next_page=self.next_page,
        )
        return d


class BlogPost(Post):
    def __init__(self, filename, post):
        super(BlogPost, self).__init__(post.content, post.handler, **post.metadata)
        self.filename = filename
        self.name = os.path.splitext(filename)[0]
        self.metadata['uuid'] = self.metadata['uuid'] if 'uuid' in self.metadata else str(uuid.uuid4())
        self.next = None
        self.previous = None

    @property
    def categories(self):
        return [v for v in self.metadata.get('categories', '').split(' ') if v]

    @property
    def tags(self):
        return [v for v in self.metadata.get('tags', '').split(' ') if v]

    @property
    def keywords(self):
        return [v for v in self.metadata.get('keywords', '').split(' ') if v]

    def convert_post_url(self, data):
        def repl(match):
            name = match.group(1)
            post = BlogSite().posts[name]
            return '({})'.format(reverse('post', args=(post.url,), host='blog'))

        p = re.compile(r'\(post-url/(\d{4}-\d{2}-\d{2}-.+)\)')
        return p.sub(repl, data)

    def convert_post_assets(self, data):
        return data.replace(r'post-assets/', settings.STATIC_URL)

    @classmethod
    def markdown_to_html(cls, data):
        data = markdown.markdown(
            data,
            output_format='html5',
            extensions=[
                'pymdownx.extra',
                'pymdownx.highlight',
                'pymdownx.arithmatex',
                'pymdownx.tilde',
                'pymdownx.tasklist',
                'pymdownx.magiclink',
                'pymdownx.superfences',
                'nl2br',
            ],
            extension_configs={
                'pymdownx.highlight': {
                    'noclasses'     : True,
                    'pygments_style': 'github',
                },
                "pymdownx.superfences": {
                    "custom_fences": [
                        {
                            'name'  : 'flow',
                            'class' : 'uml-flowchart',
                            'format': pymdownx.superfences.fence_code_format
                        },
                        {
                            'name'  : 'sequence',
                            'class' : 'uml-sequence-diagram',
                            'format': pymdownx.superfences.fence_code_format
                        }
                    ]
                }
            }
        )
        return data

    @property
    @functools.lru_cache()
    def url(self):
        output_dir = ''
        for c in self.categories:
            output_dir = os.path.join(output_dir, c)

        splits = self.name.split('-', maxsplit=3)
        for path in splits[:-1]:
            output_dir = os.path.join(output_dir, path)
        else:
            output_filename = '{}.html'.format(splits[-1])

        return os.path.join(output_dir, output_filename)

    @functools.lru_cache()
    def to_dict(self, nested=True):
        d = self.metadata.copy()
        d['categories'] = self.categories
        d['tags'] = self.tags
        d['keywords'] = self.keywords
        content = self.markdown_to_html(self.convert_post_url(self.convert_post_assets(self.content)))
        d['content'] = content
        d['excerpt'] = content.split(app_config.excerpt_separator)[0]
        d['url'] = self.url
        if self.previous and nested:
            d['previous'] = self.previous.to_dict(nested=False)
        if self.next and nested:
            d['next'] = self.next.to_dict(nested=False)
        return d


class BlogCategory(object):
    def __init__(self, name):
        self.name = name
        self.posts = OrderedDict()

    @property
    @functools.lru_cache()
    def url(self):
        return 'categories/{}.html'.format(self.name)

    @functools.lru_cache()
    def to_dict(self):
        d = dict(
            posts=[post.to_dict() for post in reversed(self.posts.values())],
            name=self.name,
            url=self.url,
        )
        return d


class BlogTag(object):
    def __init__(self, name):
        self.name = name
        self.posts = OrderedDict()

    @property
    @functools.lru_cache()
    def url(self):
        return 'tags/{}.html'.format(self.name)

    @functools.lru_cache()
    def to_dict(self):
        d = dict(
            posts=[post.to_dict() for post in reversed(self.posts.values())],
            name=self.name,
            url=self.url,
        )
        return d
