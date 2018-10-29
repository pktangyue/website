from django.conf import settings
from django_hosts import host

host_patterns = [
    host(r'www', settings.ROOT_URLCONF, name='www'),
    host(r'blog', 'blog.urls', name='blog'),
    host(r'note', 'note.urls', name='note'),
    host(r'assets', 'website.static_urls', name='assets'),
]
