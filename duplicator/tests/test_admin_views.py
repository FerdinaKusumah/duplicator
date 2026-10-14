from django.contrib.auth.models import Permission, User
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse

from duplicator.tests.dummy_models import CloneModel, UniqueModel


def duplicate_url(obj) -> str:
    opts = obj._meta
    return reverse(
        f"test_admin:{opts.app_label}_{opts.model_name}_duplicate", args=[obj.pk]
    )


def changelist_url(model) -> str:
    opts = model._meta
    return reverse(f"test_admin:{opts.app_label}_{opts.model_name}_changelist")


def staff_with(*codenames: str) -> User:
    user = User.objects.create_user(
        username="_".join(codenames) or "staff", password="x", is_staff=True
    )
    user.user_permissions.set(Permission.objects.filter(codename__in=codenames))
    return user


@override_settings(ROOT_URLCONF="duplicator.tests.urls")
class DuplicateViewTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="x")
        self.client.force_login(self.admin)
        self.obj = CloneModel.objects.create(name="Item", value=1)

    def test_get_does_not_duplicate(self):
        response = self.client.get(duplicate_url(self.obj))
        self.assertEqual(response.status_code, 405)
        self.assertEqual(CloneModel.objects.count(), 1)

    def test_post_duplicates_and_opens_the_copy(self):
        response = self.client.post(duplicate_url(self.obj))
        copy = CloneModel.objects.latest("pk")
        self.assertNotEqual(copy.pk, self.obj.pk)
        self.assertRedirects(
            response,
            reverse("test_admin:duplicator_clonemodel_change", args=[copy.pk]),
            fetch_redirect_response=False,
        )

    def test_without_add_permission_is_forbidden(self):
        self.client.force_login(staff_with("view_clonemodel", "change_clonemodel"))
        response = self.client.post(duplicate_url(self.obj))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(CloneModel.objects.count(), 1)

    def test_without_view_or_change_permission_is_forbidden(self):
        self.client.force_login(staff_with("add_clonemodel"))
        response = self.client.post(duplicate_url(self.obj))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(CloneModel.objects.count(), 1)

    def test_a_missing_object_redirects(self):
        response = self.client.post(
            duplicate_url(self.obj).replace(f"/{self.obj.pk}/", "/999/")
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CloneModel.objects.count(), 1)

    def test_a_database_error_is_reported_not_raised(self):
        unique = UniqueModel.objects.create(name="Item", slug="item")
        response = self.client.post(duplicate_url(unique))
        self.assertRedirects(
            response,
            reverse("test_admin:duplicator_uniquemodel_change", args=[unique.pk]),
            fetch_redirect_response=False,
        )
        self.assertEqual(UniqueModel.objects.count(), 1)
        self.assertIn(
            "Could not duplicate",
            [str(m) for m in get_messages(response.wsgi_request)][0],
        )

    def test_the_change_form_posts_to_the_duplicate_url(self):
        response = self.client.get(
            reverse("test_admin:duplicator_clonemodel_change", args=[self.obj.pk])
        )
        self.assertContains(response, f'formaction="{duplicate_url(self.obj)}')
        self.assertContains(response, 'formmethod="post"')


@override_settings(ROOT_URLCONF="duplicator.tests.urls")
class DuplicateActionTest(TestCase):
    def setUp(self):
        self.client.force_login(
            User.objects.create_superuser(username="admin", password="x")
        )

    def run_action(self, model, objects):
        action = f"duplicate_{model._meta.model_name}_selected"
        return self.client.post(
            changelist_url(model),
            {"action": action, "_selected_action": [o.pk for o in objects]},
            follow=True,
        )

    def test_one_record_is_singular(self):
        unique = UniqueModel.objects.create(name="A", slug="a")
        UniqueModel.DUPLICATOR_EXCLUDE_FIELDS = ["slug"]
        try:
            response = self.run_action(UniqueModel, [unique])
        finally:
            UniqueModel.DUPLICATOR_EXCLUDE_FIELDS = []
        self.assertContains(response, "Successfully duplicated 1 record.")

    def test_a_database_error_rolls_back_and_is_reported(self):
        objects = [UniqueModel.objects.create(name=n, slug=n) for n in ("a", "b")]
        response = self.run_action(UniqueModel, objects)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nothing was duplicated")
        self.assertEqual(UniqueModel.objects.count(), 2)


class AdminSetupTest(TestCase):
    def test_a_model_without_the_mixin_is_rejected(self):
        from django.contrib.admin.sites import AdminSite
        from django.core.exceptions import ImproperlyConfigured

        from duplicator.admin import DuplicatorAdminMixin
        from duplicator.tests.dummy_models import Author

        with self.assertRaisesMessage(
            ImproperlyConfigured, "must inherit DuplicatorMixin"
        ):
            DuplicatorAdminMixin(Author, AdminSite())
