from django.db import models

from duplicator.models import DuplicatorMixin


class TestModel(DuplicatorMixin, models.Model):
    name = models.CharField(max_length=100)
    counter = models.IntegerField(default=1)

    class Meta:
        app_label = "duplicator"
        verbose_name = "Test Model"


class CloneModel(DuplicatorMixin, models.Model):
    name = models.CharField(max_length=100)
    value = models.IntegerField(default=10)

    class Meta:
        app_label = "duplicator"
        verbose_name = "Clone Test Model"

    def clone(self, commit=True, **kwargs):
        new_instance = super().clone(commit=False, **kwargs)
        if hasattr(new_instance, "name"):
            new_instance.name = "CUSTOM-CLONED: CLONED - {}".format(self.name)

        if commit:
            new_instance.save()

        return new_instance


class NoCloneModel(DuplicatorMixin, models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "duplicator"
        verbose_name = "No Clone Test Model"


class UniqueModel(DuplicatorMixin, models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        app_label = "duplicator"


class OptionalNameModel(DuplicatorMixin, models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        app_label = "duplicator"


class Author(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "duplicator"


class Tag(models.Model):
    label = models.CharField(max_length=100)

    class Meta:
        app_label = "duplicator"


class Membership(models.Model):
    book = models.ForeignKey("Book", on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        app_label = "duplicator"


class Book(DuplicatorMixin, models.Model):
    name = models.CharField(max_length=20)
    author = models.ForeignKey(Author, null=True, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, blank=True, related_name="books")
    featured_tags = models.ManyToManyField(Tag, blank=True, related_name="featured_in")
    memberships = models.ManyToManyField(
        Tag, through=Membership, related_name="member_books"
    )

    class Meta:
        app_label = "duplicator"


class Place(DuplicatorMixin, models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "duplicator"


class Restaurant(Place):
    serves_pizza = models.BooleanField(default=False)

    class Meta:
        app_label = "duplicator"


class PlainModel(DuplicatorMixin, models.Model):
    name = models.CharField(max_length=100)


class NoNameModel(DuplicatorMixin, models.Model):
    title = models.CharField(max_length=100)

    class Meta:
        app_label = "duplicator"
