from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.shortcuts import redirect
from django.urls import path
from django.utils.translation import gettext_lazy as _


@admin.action(description=_("Duplicate selected %(verbose_name_plural)s"))
@transaction.atomic
def duplicate_selected_objects(model_admin, request, queryset):
    if not model_admin.has_add_permission(request):
        model_admin.message_user(
            request,
            _("You do not have permission to duplicate these objects."),
            level=messages.ERROR,
        )
        return

    dup_count = 0
    for obj in queryset:
        obj.clone()
        dup_count += 1

    model_admin.message_user(
        request,
        _("Successfully duplicated %d records" % dup_count),
        level=messages.SUCCESS,
    )


class DuplicatorAdminMixin(admin.ModelAdmin):
    change_form_template = "admin/duplicator/change_form.html"
    actions = [duplicate_selected_objects]

    def __init__(self, model, admin_site):
        app_is_installed = False
        app_config_name = "duplicator"

        for app in settings.INSTALLED_APPS:
            if app == app_config_name or app.startswith(f"{app_config_name}.apps."):
                app_is_installed = True
                break

        if not app_is_installed:
            raise ImproperlyConfigured(
                "The 'duplicator' app must be added to your INSTALLED_APPS "
                "in settings.py to correctly load the necessary templates and actions. "
                f"(Error source: {self.__class__.__name__})"
            )

        super().__init__(model, admin_site)

        if not hasattr(model, "clone"):
            raise ImproperlyConfigured(
                f"Model {model.__name__} must inherit DuplicatorMixin "
                f"to use DuplicatorAdminMixin."
            )

        # prevent error duplicate action names
        new_actions = []
        for action in self.actions:
            if not action is duplicate_selected_objects:
                new_actions.append(action)
                continue

            model_name = self.model._meta.model_name
            unique_action_name = f"duplicate_{model_name}_selected"

            def unique_action(model_admin, request, queryset):
                return duplicate_selected_objects(model_admin, request, queryset)

            unique_action.__name__ = unique_action_name
            unique_action.short_description = (
                duplicate_selected_objects.short_description
            )
            new_actions.append(unique_action)

        self.actions = tuple(new_actions)

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
        new_object = original_object.clone()

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
