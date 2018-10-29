from django.conf import settings
from django.conf.urls.static import static

urlpatterns = static('/', document_root=settings.STATIC_ROOT)
