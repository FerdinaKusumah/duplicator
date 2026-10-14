from django.test import TestCase

from duplicator.tests.dummy_models import (
    Author,
    Book,
    Membership,
    OptionalNameModel,
    Place,
    Restaurant,
    Tag,
)


class CloneFieldsTest(TestCase):
    def setUp(self):
        self.author = Author.objects.create(name="Ann")
        self.book = Book.objects.create(name="Book", author=self.author)

    def test_foreign_keys_are_copied_without_loading_the_related_object(self):
        book = Book.objects.get(pk=self.book.pk)
        with self.assertNumQueries(0):
            copy = book.clone(commit=False)
        self.assertEqual(copy.author_id, self.author.pk)

    def test_an_empty_name_is_not_marked_as_copy(self):
        original = OptionalNameModel.objects.create(name=None)
        self.assertIsNone(original.clone().name)

    def test_the_copy_suffix_fits_the_name_field(self):
        original = Book.objects.create(name="A" * 20)
        copy = original.clone()
        self.assertEqual(len(copy.name), 20)
        self.assertTrue(copy.name.endswith(" (Copy)"))


class CloneManyToManyTest(TestCase):
    def setUp(self):
        self.tags = [Tag.objects.create(label=label) for label in ("a", "b")]
        self.book = Book.objects.create(name="Book")
        self.book.tags.set(self.tags)
        self.book.featured_tags.set(self.tags[:1])
        Membership.objects.create(book=self.book, tag=self.tags[0])

    def tearDown(self):
        Book.DUPLICATOR_EXCLUDE_FIELDS = []

    def test_many_to_many_relations_are_copied(self):
        copy = self.book.clone()
        self.assertEqual(set(copy.tags.all()), set(self.tags))
        self.assertEqual(set(copy.featured_tags.all()), set(self.tags[:1]))

    def test_excluded_many_to_many_fields_are_not_copied(self):
        Book.DUPLICATOR_EXCLUDE_FIELDS = ["featured_tags"]
        copy = self.book.clone()
        self.assertEqual(copy.featured_tags.count(), 0)
        self.assertEqual(copy.tags.count(), 2)

    def test_relations_with_a_custom_through_model_are_left_alone(self):
        copy = self.book.clone()
        self.assertEqual(copy.memberships.count(), 0)
        self.assertEqual(Membership.objects.count(), 1)

    def test_commit_false_copies_relations_once_saved(self):
        copy = self.book.clone(commit=False)
        copy.save()
        self.book.copy_many_to_many(copy)
        self.assertEqual(copy.tags.count(), 2)


class CloneInheritanceTest(TestCase):
    def test_cloning_a_child_model_leaves_the_original_parent_untouched(self):
        original = Restaurant.objects.create(name="Pizzeria", serves_pizza=True)
        copy = original.clone()
        original.refresh_from_db()
        self.assertEqual(original.name, "Pizzeria")
        self.assertNotEqual(copy.pk, original.pk)
        self.assertEqual(Place.objects.count(), 2)
        self.assertEqual(Restaurant.objects.count(), 2)
        self.assertTrue(Restaurant.objects.get(pk=copy.pk).serves_pizza)


class MixinMetaTest(TestCase):
    def test_a_model_without_its_own_meta_stays_concrete(self):
        from duplicator.tests.dummy_models import PlainModel

        self.assertFalse(PlainModel._meta.abstract)
        self.assertEqual(PlainModel.objects.create(name="A").clone().name, "A (Copy)")


class NoNameFieldTest(TestCase):
    def test_a_model_without_a_name_field_is_copied_as_is(self):
        from duplicator.tests.dummy_models import NoNameModel

        self.assertEqual(NoNameModel.objects.create(title="T").clone().title, "T")
