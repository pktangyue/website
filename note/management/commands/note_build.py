import argparse
import os
from shutil import copy2

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from note.apps import NoteConfig
from note.models import Note
from note.quiver2html.objects import QV_TYPES
from note.quiver2html.objects.factory import QvFactory

app_config: NoteConfig = apps.get_app_config('note')


class StoreDict(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        ret = {}
        for s in values:
            key, value = s.split('=')
            ret[key] = value
        setattr(namespace, self.dest, ret)


class Command(BaseCommand):
    help = 'build note'

    def add_arguments(self, parser):
        parser.add_argument(
            'notes',
            nargs='+',
            help='.qvlibrary or .qvnotebook or .qvnote dir',
        )

    def handle(self, *args, **options):
        print(options)
        Note.objects.update(active=False)
        for note in options.get('notes', []):
            QvFactory.create(note).parse(
                os.path.join(app_config.path, 'templates/note/note.html'),
                os.path.join(app_config.path, 'template_strings', 'note'),
                resources_url=settings.STATIC_URL + 'resources',
                write_file_func=self.write_file_func,
            )

    def write_file_func(self, template, output, filename, context, resources=None):
        context['active'] = 'note'
        output_html = render_to_string(template, context)
        with open(os.path.join(output, filename), mode='w', encoding='UTF-8') as f:
            f.write(output_html)
        # export resources
        if resources:
            resources_dir = os.path.join(app_config.path, 'static', 'resources')
            os.makedirs(resources_dir, exist_ok=True)
            for resource in resources:
                copy2(resource.path, resources_dir)

        ins = context['ins']
        if ins.type == QV_TYPES.NOTE:
            Note.objects.update_or_create(uuid=ins.uuid, defaults=dict(
                title=ins.name,
                category=ins.parent.name,
                tags=ins.tags,
                content=context['content'],
                active=True,
                create_datetime=ins.create_datetime,
                update_datetime=ins.update_datetime,
            ))
