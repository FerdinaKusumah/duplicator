from copy import copy


class DuplicatorMixin(object):
    """
    Base mixin to add cloning capabilities to a Django model.
    It provides a base clone method that performs a shallow copy,
    resets the primary key, and saves the new object.
    """

    class Meta:
        abstract = True

    def clone(self, commit=True, **kwargs):
        # clone instance
        new_instance = copy(self)

        # remove id
        new_instance.pk = None

        # flag if record have name
        if hasattr(new_instance, "name"):
            new_instance.name = "{} (Copy)".format(new_instance.name)

        # add kwargs if any
        for key, value in kwargs.items():
            setattr(new_instance, key, value)

        if commit:
            # save new instance
            new_instance.save()

        return new_instance
