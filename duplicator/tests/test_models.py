from django.test import TestCase

from duplicator.tests.dummy_models import TestModel, CloneModel, NoCloneModel


class DuplicatorMixinTest(TestCase):

    def setUp(self):
        self.original_obj = TestModel.objects.create(
            name="Original Project Name", counter=10
        )
        self.initial_count = TestModel.objects.count()

    def test_01_clone_with_default_commit(self):
        new_obj = self.original_obj.clone()

        self.assertIsNotNone(new_obj.pk)
        self.assertNotEqual(new_obj.pk, self.original_obj.pk)
        self.assertEqual(TestModel.objects.count(), self.initial_count + 1)

        expected_name = "Original Project Name (Copy)"
        self.assertEqual(new_obj.name, expected_name)
        self.assertEqual(new_obj.counter, self.original_obj.counter)

    def test_02_clone_with_commit_false(self):
        new_obj = self.original_obj.clone(commit=False)

        self.assertIsNone(new_obj.pk)
        self.assertEqual(TestModel.objects.count(), self.initial_count)

        expected_name = "Original Project Name (Copy)"
        self.assertEqual(new_obj.name, expected_name)

        new_obj.save()
        self.assertIsNotNone(new_obj.pk)
        self.assertEqual(TestModel.objects.count(), self.initial_count + 1)

    def test_03_clone_with_kwargs_override(self):
        new_obj = self.original_obj.clone(counter=99, name="Forced Name by Kwargs")

        self.assertEqual(new_obj.counter, 99)
        self.assertEqual(new_obj.name, "Forced Name by Kwargs")
        self.assertEqual(TestModel.objects.count(), self.initial_count + 1)

    def test_04_clone_with_extra_kwargs(self):
        new_obj = self.original_obj.clone(new_attr="Hello World")

        self.assertTrue(hasattr(new_obj, "new_attr"))
        self.assertEqual(new_obj.new_attr, "Hello World")
        self.assertEqual(TestModel.objects.count(), self.initial_count + 1)


class DuplicatorExcludeTests(TestCase):

    def setUp(self):
        self.original_obj = TestModel.objects.create(name="Simple Item", counter=5)
        self.clone_obj = CloneModel.objects.create(name="Custom Item", value=50)
        self.initial_count = TestModel.objects.count() + CloneModel.objects.count()

    def test_05_field_excluded_and_reset_to_default(self):
        TestModel.DUPLICATOR_EXCLUDE_FIELDS = ["counter"]

        new_obj = self.original_obj.clone()
        self.assertEqual(new_obj.name, "Simple Item (Copy)")
        self.assertNotEqual(new_obj.counter, self.original_obj.counter)
        self.assertEqual(new_obj.counter, 1)
        TestModel.DUPLICATOR_EXCLUDE_FIELDS = []

    def test_06_excluded_field_can_be_overridden_by_kwargs(self):
        TestModel.DUPLICATOR_EXCLUDE_FIELDS = ["counter"]

        new_obj = self.original_obj.clone(counter=999)
        self.assertEqual(new_obj.counter, 999)
        TestModel.DUPLICATOR_EXCLUDE_FIELDS = []

    def test_07_custom_clone_method_is_applied(self):
        new_obj = self.clone_obj.clone()

        expected_name = "CUSTOM-CLONED: CLONED - Custom Item"
        self.assertEqual(new_obj.name, expected_name)
        self.assertEqual(new_obj.value, self.clone_obj.value)
        self.assertNotEqual(new_obj.pk, self.clone_obj.pk)

    def test_08_custom_clone_method_handles_kwargs(self):
        new_obj = self.clone_obj.clone(name="Force New Name")

        expected_name = "CUSTOM-CLONED: CLONED - Custom Item"
        self.assertEqual(new_obj.name, expected_name)

    def test_09_no_clone_model_uses_base_mixin(self):
        original_no_clone = NoCloneModel.objects.create(name="No Custom Logic")
        new_obj = original_no_clone.clone()

        expected_name = "No Custom Logic (Copy)"
        self.assertEqual(new_obj.name, expected_name)
        self.assertNotEqual(new_obj.pk, original_no_clone.pk)
