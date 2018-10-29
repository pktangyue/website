from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = 'index.html'
    template_engine = 'dummy'


class BlogView(TemplateView):
    template_engine = 'dummy'

    def get(self, request, path):
        self.template_name = path
        return super(BlogView, self).get(request)
