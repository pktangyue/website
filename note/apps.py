from django.apps import AppConfig


class NoteConfig(AppConfig):
    name = 'note'

    def to_dict(self):
        keys = (
            'name',
        )

        return {k: getattr(self, k, None) for k in keys}
