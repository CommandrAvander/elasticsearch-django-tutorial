from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from core.views import autocomplete_view, student_detail, HomePageView


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^autocomplete/', autocomplete_view, name='autocomplete-view'),
    url(r'^student', student_detail, name='student-detail'),
    url(r'^$', HomePageView.as_view(), name='index-view'),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
