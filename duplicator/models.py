from typing import Any

from django.core.exceptions import FieldDoesNotExist
from django.db import models

COPY_SUFFIX = " (Copy)"
NAME_FIELD = "name"
TEXT_FIELDS = (models.CharField, models.TextField)


class DuplicatorMixin:
    """
    Base mixin to add cloning capabilities to a Django model.
    It copies the concrete fields and many-to-many relations, leaves every
    primary key (including inherited parents') unset, and saves the new object.
    """

    DUPLICATOR_EXCLUDE_FIELDS: list[str] = []

    def clone(self, commit: bool = True, **kwargs: Any) -> models.Model:
        exclude = set(self.DUPLICATOR_EXCLUDE_FIELDS)
        new_instance = self.__class__()

        for field in self._meta.concrete_fields:
            if field.primary_key or field.name in exclude:
                continue
            setattr(new_instance, field.attname, getattr(self, field.attname))

        self._mark_as_copy(new_instance, exclude)

        for key, value in kwargs.items():
            setattr(new_instance, key, value)

        new_instance.pk = None

        if commit:
            new_instance.save()
            self.copy_many_to_many(new_instance)

        return new_instance

    def copy_many_to_many(self, target: models.Model) -> None:
        """Give a saved copy the same many-to-many relations, except custom `through` ones."""
        exclude = set(self.DUPLICATOR_EXCLUDE_FIELDS)
        for field in self._meta.many_to_many:
            if (
                field.name in exclude
                or not field.remote_field.through._meta.auto_created
            ):
                continue
            getattr(target, field.name).set(getattr(self, field.name).all())

    def _mark_as_copy(self, target: models.Model, exclude: set[str]) -> None:
        try:
            field = self._meta.get_field(NAME_FIELD)
        except FieldDoesNotExist:
            return
        value = getattr(target, field.attname)
        if field.name in exclude or not isinstance(field, TEXT_FIELDS) or not value:
            return
        if field.max_length:
            value = value[: field.max_length - len(COPY_SUFFIX)]
        setattr(target, field.attname, f"{value}{COPY_SUFFIX}")
