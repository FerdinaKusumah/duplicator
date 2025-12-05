from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.test import TestCase, RequestFactory, override_settings

from duplicator.admin import DuplicatorAdminMixin
from duplicator.admin import duplicate_selected_objects
from duplicator.tests.dummy_models import CloneModel, NoCloneModel

test_site = AdminSite(name="test_admin")


def duplicate_clone_model_action(modeladmin, request, queryset):
    return duplicate_selected_objects(modeladmin, request, queryset)


def duplicate_noclonemodel_action(modeladmin, request, queryset):
    return duplicate_selected_objects(modeladmin, request, queryset)


duplicate_clone_model_action.short_description = "Duplicate selected clone objects"
duplicate_noclonemodel_action.short_description = "Duplicate selected no-clone objects"


class CloneModelAdmin(DuplicatorAdminMixin, admin.ModelAdmin):
    list_display = ("name", "value")
    duplicate_clone = duplicate_clone_model_action
    actions = ["duplicate_clone"]


class NoCloneModelAdmin(DuplicatorAdminMixin, admin.ModelAdmin):
    list_display = ("name",)
    duplicate_clone = duplicate_noclonemodel_action
    actions = ["duplicate_clone"]


test_site.register(CloneModel, CloneModelAdmin)
test_site.register(NoCloneModel, NoCloneModelAdmin)


@override_settings(ROOT_URLCONF="duplicator.tests.urls")
class DuplicatorAdminCoreTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testadmin", password="password", is_staff=True, is_superuser=True
        )
        self.no_perm_user = User.objects.create_user(
            username="noperm", password="password", is_staff=True
        )
        self.site = test_site
        self.factory = RequestFactory()

    def _create_request(self, user=None, method="post", path="/admin/"):
        request = self.factory.generic(method, path)
        request.user = user if user else self.user

        SessionMiddleware(lambda req: None).process_request(request)
        MessageMiddleware(lambda req: None).process_request(request)
        request.session.save()
        return request


class DuplicatorClonePathTest(DuplicatorAdminCoreTest):
    def setUp(self):
        super().setUp()
        self.model_admin = CloneModelAdmin(CloneModel, self.site)
        self.obj_orig = CloneModel.objects.create(name="Custom Item A", value=100)
        self.url_name = "admin:duplicator_clonemodel_duplicate"

    def test_01_duplicate_view_success(self):

        request = self._create_request()

        response = self.model_admin.duplicate_view(request, str(self.obj_orig.pk))

        self.assertEqual(response.status_code, 302)
        new_obj = CloneModel.objects.latest("pk")

        self.assertTrue(new_obj.name.startswith("CUSTOM-CLONED: CLONED - "))
        self.assertEqual(CloneModel.objects.count(), 2)

    def test_02_duplicate_view_no_permission(self):
        request = self._create_request(user=self.no_perm_user)
        self.model_admin.duplicate_view(request, str(self.obj_orig.pk))
        self.assertEqual(CloneModel.objects.count(), 1)

    def test_03_duplicate_selected_objects_action_success(self):
        CloneModel.objects.create(name="Custom Item B", value=200)

        queryset = CloneModel.objects.all()
        request = self._create_request()

        self.model_admin.duplicate_clone(request, queryset)
        self.assertEqual(CloneModel.objects.count(), 4)

        cloned_count = CloneModel.objects.filter(
            name__startswith="CUSTOM-CLONED: "
        ).count()
        self.assertEqual(cloned_count, 2)

    def test_04_duplicate_selected_objects_action_no_permission(self):
        CloneModel.objects.create(name="Custom Item B", value=200)

        queryset = CloneModel.objects.all()
        request = self._create_request(user=self.no_perm_user)

        duplicate_selected_objects(self.model_admin, request, queryset)

        self.assertEqual(CloneModel.objects.count(), 2)


class DuplicatorNoClonePathTest(DuplicatorAdminCoreTest):
    def setUp(self):
        super().setUp()
        self.model_admin = NoCloneModelAdmin(NoCloneModel, self.site)
        self.obj_orig = NoCloneModel.objects.create(name="Original Fallback Item")
        self.url_name = "admin:duplicator_noclonemodel_duplicate"

    def test_05_duplicate_view_fallback_success(self):

        request = self._create_request()

        response = self.model_admin.duplicate_view(request, str(self.obj_orig.pk))

        self.assertEqual(response.status_code, 302)
        new_obj = NoCloneModel.objects.latest("pk")

        self.assertTrue(new_obj.name.endswith(" (Copy)"))
        self.assertEqual(NoCloneModel.objects.count(), 2)

    def test_06_duplicate_selected_objects_action_fallback(self):
        NoCloneModel.objects.create(name="Second Fallback Item")
        queryset = NoCloneModel.objects.all()
        request = self._create_request()

        self.model_admin.duplicate_clone(request, queryset)
        self.assertEqual(NoCloneModel.objects.count(), 4)
        cloned_count = NoCloneModel.objects.filter(name__endswith=" (Copy)").count()
        self.assertEqual(cloned_count, 2)


class DuplicatorMixinInitTest(TestCase):
    def test_07_improperly_configured_check(self):

        class SimpleTestModel(models.Model):
            class Meta:
                app_label = "duplicator"
                managed = False

        class SimpleSite(AdminSite):
            pass

        with self.settings(INSTALLED_APPS=[]):
            with self.assertRaises(ImproperlyConfigured) as context:
                DuplicatorAdminMixin(SimpleTestModel, SimpleSite())

            self.assertIn(
                "The 'duplicator' app must be added to your INSTALLED_APPS",
                str(context.exception),
            )
