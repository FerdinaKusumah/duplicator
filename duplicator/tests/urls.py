from django.urls import path, include

from duplicator.tests.test_admin import test_site

urlpatterns = [
    path(
        "admin/",
        include((test_site.urls[0], test_site.urls[1]), namespace=test_site.urls[2]),
    ),
]
