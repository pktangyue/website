import os

from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = 'note/index.html'
    template_engine = 'dummy'

class NoteView(TemplateView):
    template_engine = 'dummy'

    def get(self, request, path):
        self.template_name = os.path.join('note', path)
        return super(NoteView, self).get(request)
