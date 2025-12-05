from django.test import TestCase

from duplicator.tests.dummy_models import TestModel


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
