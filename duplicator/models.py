class DuplicatorMixin(object):
    """
    Base mixin to add cloning capabilities to a Django model.
    It provides a base clone method that performs a shallow copy,
    resets the primary key, and saves the new object.
    """

    DUPLICATOR_EXCLUDE_FIELDS = []

    class Meta:
        abstract = True

    def clone(self, commit=True, **kwargs):
        # get exclude list
        exclude_fields = set(
            list(getattr(self, "DUPLICATOR_EXCLUDE_FIELDS", [])) + [self._meta.pk.name]
        )

        # clone instance
        new_instance = self.__class__()

        for field in self._meta.fields:
            field_name = field.name

            if field_name not in exclude_fields:
                setattr(new_instance, field_name, getattr(self, field_name))

        # flag if record have name
        if hasattr(new_instance, "name") and "name" not in exclude_fields:
            new_instance.name = "{} (Copy)".format(new_instance.name)

        # add kwargs if any
        for key, value in kwargs.items():
            setattr(new_instance, key, value)

        # remove id for safety
        new_instance.pk = None

        if commit:
            # save new instance
            new_instance.save()

        return new_instance
