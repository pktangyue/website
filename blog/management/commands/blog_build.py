import os
import time

import frontmatter
import pendulum
from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from frontmatter import YAMLHandler, u
from ruamel import yaml
from tqdm import tqdm
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from blog.models import Post
from blog.objects import BlogPost, BlogSite, app_config


class RuamelYamlHandler(YAMLHandler):
    def load(self, fm, **kwargs):
        """
        Parse YAML front matter. This uses yaml.SafeLoader by default.
        """
        kwargs.setdefault('Loader', yaml.RoundTripLoader)
        return yaml.load(fm, **kwargs)

    def export(self, metadata, **kwargs):
        """
        Export metadata as YAML. This uses yaml.SafeDumper by default.
        """
        kwargs.setdefault('Dumper', yaml.RoundTripDumper)
        kwargs.setdefault('default_flow_style', False)

        metadata = yaml.dump(metadata, **kwargs).strip()
        return u(metadata)  # ensure unicode


class StaticWatchHandler(PatternMatchingEventHandler):

    def __init__(self, command):
        self.command = command
        super(StaticWatchHandler, self).__init__(patterns=['*.js', '*.scss', '*.html'], ignore_directories=True)

    def on_any_event(self, event):
        self.command.build()


class Command(BaseCommand):
    help = 'build blog'

    def __init__(self, *args, **kwargs):
        self.blog_site = BlogSite()
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument(
            '-w',
            '--watch',
            action='store_true',
            help='Watch for changes and rebuild',
        )

    def handle(self, *args, **options):
        self.parse_posts()
        self.build()
        self.dump_posts()
        self.save_to_db()
        if options.get('watch', False):
            self.watch_static()

    def watch_static(self):
        # 注册watchdog
        static_event_handler = StaticWatchHandler(self)
        observer = Observer()
        observer.schedule(static_event_handler, os.path.join(app_config.path, 'templates'), recursive=True)
        observer.schedule(static_event_handler, os.path.join(settings.BASE_DIR, 'templates'), recursive=True)
        observer.schedule(static_event_handler, os.path.join(settings.BASE_DIR, 'static'), recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    def parse_posts(self):
        self.stdout.write('解析 post...')
        post_path = os.path.join(app_config.path, 'posts')
        for filename in tqdm(sorted(os.listdir(post_path))):
            if os.path.splitext(filename)[1] in ('.md', '.markdown'):
                post = BlogPost(filename, frontmatter.load(os.path.join(post_path, filename), handler=RuamelYamlHandler()))
                self.blog_site.add_post(post)

    def get_output_filename(self, url):
        output_filename = os.path.join(app_config.path, 'template_strings', url)
        output_dir, _ = os.path.split(output_filename)
        os.makedirs(output_dir, exist_ok=True)
        return output_filename

    def build(self):
        self.build_posts()
        self.build_indexes()
        self.build_categories()
        self.build_tags()

    def build_posts(self):
        self.stdout.write('生成 post...')
        for post in tqdm(self.blog_site.posts.values()):
            output_html = render_to_string('post.html', {
                'post'  : post.to_dict(),
                'site'  : self.blog_site.to_dict(),
                'active': 'blog',
            })
            output_filename = self.get_output_filename(post.url)
            with open(output_filename, mode='w', encoding='UTF-8') as f:
                f.write(output_html)

    def build_indexes(self):
        self.stdout.write('生成 index...')
        for paginate_page in tqdm(self.blog_site):
            output_html = render_to_string('index.html', {
                'paginator': paginate_page.to_dict(),
                'site'     : self.blog_site.to_dict(),
                'active'   : 'blog',
            })
            output_filename = self.get_output_filename(paginate_page.url)
            with open(output_filename, mode='w', encoding='UTF-8') as f:
                f.write(output_html)

    def build_categories(self):
        self.stdout.write('生成 categories...')
        for category in tqdm(self.blog_site.categories.values()):
            output_html = render_to_string('categories.html', {
                'category': category.to_dict(),
                'site'    : self.blog_site.to_dict(),
                'active'  : 'blog',
            })
            output_filename = self.get_output_filename(category.url)
            with open(output_filename, mode='w', encoding='UTF-8') as f:
                f.write(output_html)

    def build_tags(self):
        self.stdout.write('生成 tags...')
        for tag in tqdm(self.blog_site.tags.values()):
            output_html = render_to_string('tags.html', {
                'tag'   : tag.to_dict(),
                'site'  : self.blog_site.to_dict(),
                'active': 'blog',
            })
            output_filename = self.get_output_filename(tag.url)
            with open(output_filename, mode='w', encoding='UTF-8') as f:
                f.write(output_html)

    def dump_posts(self):
        self.stdout.write('更新 post...')
        post_path = os.path.join(app_config.path, 'posts')
        for post in tqdm(self.blog_site.posts.values()):
            with open(os.path.join(post_path, post.filename), mode='wb') as f:
                frontmatter.dump(post, f, handler=RuamelYamlHandler(), allow_unicode=True)

    def save_to_db(self):
        Post.objects.update(active=False)
        self.stdout.write('保存 post...')
        for post in tqdm(self.blog_site.posts.values()):
            d = post.metadata.copy()
            d.pop('layout')
            Post.objects.update_or_create(uuid=post.metadata['uuid'], defaults=dict(
                uuid=post.metadata.get('uuid'),
                date=pendulum.instance(post.metadata.get('date'), tz=settings.TIME_ZONE),
                title=post.metadata.get('title'),
                subtitle=post.metadata.get('subtitle'),
                categories=post.categories,
                tags=post.tags,
                keywords=post.keywords,
                content=post.content,
                active=True,
            ))
