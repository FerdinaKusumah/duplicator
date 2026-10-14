from django.apps import apps
from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import (
    ImproperlyConfigured,
    PermissionDenied,
    ValidationError,
)
from django.db import DatabaseError, models, transaction
from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import redirect
from django.urls import URLPattern, path, reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

APP_LABEL = "duplicator"
CLONE_ERRORS = (DatabaseError, ValidationError)


@admin.action(description=_("Duplicate selected %(verbose_name_plural)s"))
def duplicate_selected_objects(
    model_admin: admin.ModelAdmin, request: HttpRequest, queryset: models.QuerySet
) -> None:
    if not model_admin.has_add_permission(request):
        model_admin.message_user(
            request,
            _("You do not have permission to duplicate these objects."),
            level=messages.ERROR,
        )
        return

    try:
        with transaction.atomic():
            dup_count = 0
            for obj in queryset:
                obj.clone()
                dup_count += 1
    except CLONE_ERRORS as error:
        model_admin.message_user(
            request,
            _("Nothing was duplicated: %(error)s") % {"error": error},
            level=messages.ERROR,
        )
        return

    model_admin.message_user(
        request,
        ngettext(
            "Successfully duplicated %(count)d record.",
            "Successfully duplicated %(count)d records.",
            dup_count,
        )
        % {"count": dup_count},
        level=messages.SUCCESS,
    )


class DuplicatorAdminMixin(admin.ModelAdmin):
    change_form_template = "admin/duplicator/change_form.html"
    actions = [duplicate_selected_objects]

    def __init__(self, model: type[models.Model], admin_site: admin.AdminSite) -> None:
        if not apps.is_installed(APP_LABEL):
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
            if action is not duplicate_selected_objects:
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

    def get_urls(self) -> list[URLPattern]:
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name

        custom_urls = [
            path(
                "<path:object_id>/duplicate/",
                self.admin_site.admin_view(self.duplicate_view),
                name="%s_%s_duplicate" % info,
            ),
        ]

        return custom_urls + urls

    def duplicate_view(self, request: HttpRequest, object_id: str) -> HttpResponse:
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])

        original_object = self.get_object(request, object_id)

        # not found
        if original_object is None:
            return redirect("..")

        if not (
            self.has_add_permission(request)
            and self.has_view_or_change_permission(request, original_object)
        ):
            raise PermissionDenied

        try:
            with transaction.atomic():
                new_object = original_object.clone()
        except CLONE_ERRORS as error:
            self.message_user(
                request,
                _('Could not duplicate "%(obj)s": %(error)s')
                % {"obj": str(original_object), "error": error},
                level=messages.ERROR,
            )
            return redirect(self._change_url(original_object))

        self.message_user(
            request,
            _('Successfully duplicated object "%(obj)s".')
            % {"obj": str(original_object)},
            level=messages.SUCCESS,
        )

        return redirect(self._change_url(new_object))

    def _change_url(self, obj: models.Model) -> str:
        opts = obj._meta
        return reverse(
            f"admin:{opts.app_label}_{opts.model_name}_change",
            args=[obj.pk],
            current_app=self.admin_site.name,
        )
