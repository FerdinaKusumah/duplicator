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
