from copy import copy

from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect
from django.urls import path
from django.utils.translation import gettext_lazy as _


@admin.action(description=_("Duplicate selected %(verbose_name_plural)s"))
def duplicate_selected_objects(model_admin, request, queryset):
    if not model_admin.has_add_permission(request):
        model_admin.message_user(
            request,
            _("You do not have permission to duplicate these objects."),
            level=messages.ERROR,
        )
        return

    cnt = 0
    for obj in queryset:
        model_admin._duplicate(obj)
        cnt += 1

    model_admin.message_user(
        request, _("Successfully duplicated %d records" % cnt), level=messages.SUCCESS
    )


class DuplicatorAdminMixin(admin.ModelAdmin):
    change_form_template = "admin/duplicator/change_form.html"
    actions = [duplicate_selected_objects]

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)

        if "duplicator" not in settings.INSTALLED_APPS:
            raise ImproperlyConfigured(
                "The 'duplicator' app must be added to your INSTALLED_APPS "
                "in settings.py to correctly load the necessary templates and actions. "
                f"(Error source: {self.__class__.__name__})"
            )

    def _duplicate(self, original_object):
        if hasattr(original_object, "clone"):
            new_object = original_object.clone()
        else:
            new_object = copy(original_object)
            new_object.pk = None
            if hasattr(new_object, "name"):
                new_object.name = "{} (Copy)".format(new_object.name)

        new_object.save()
        return new_object

    def get_urls(self):
        urls = super(DuplicatorAdminMixin, self).get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name

        custom_urls = [
            path(
                "<path:object_id>/duplicate/",
                self.admin_site.admin_view(self.duplicate_view),
                name="%s_%s_duplicate" % info,
            ),
        ]

        return custom_urls + urls

    def duplicate_view(self, request, object_id):
        if not self.has_add_permission(request):
            return self.message_user(
                request,
                _("You do not have permission to duplicate this object."),
                level=messages.ERROR,
            )

        original_object = self.get_object(request, object_id)

        # not found
        if not original_object:
            return redirect("..")

        # clone object
        new_object = self._duplicate(original_object)

        self.message_user(
            request,
            _('Successfully duplicated object "%(obj)s".')
            % {"obj": str(original_object)},
            level=messages.SUCCESS,
        )

        return redirect(
            "admin:%s_%s_change"
            % (new_object._meta.app_label, new_object._meta.model_name),
            new_object.pk,
        )
