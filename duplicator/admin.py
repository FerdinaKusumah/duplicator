from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path
from django.utils.translation import gettext_lazy as _


@admin.action(description="Duplicate selected %(verbose_name_plural)s)")
def duplicate_selected_objects(modeladmin, request, queryset):
    cnt = 0
    for obj in queryset:
        if hasattr(obj, "clone"):
            obj.clone()
        else:
            obj.pk = None
            obj.save()

        cnt += 1

    modeladmin.message_user(request, _("Successfully duplicated %d records" % cnt))


class DuplicatorAdminMixin(admin.ModelAdmin):
    change_form_template = "admin/duplicator/change_form.html"
    actions = [duplicate_selected_objects]

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

    def duplicate_view(self, request, object_id, form_url=""):
        original_object = self.get_object(request, object_id)

        if not original_object:
            return redirect("..")

        if hasattr(original_object, "clone"):
            new_object = original_object.clone()
        else:
            new_object = original_object.__class__.objects.get(pk=original_object.pk)
            new_object.pk = None
            new_object.save()

        return redirect(
            "admin:%s_%s_change"
            % (new_object._meta.app_label, new_object._meta.model_name),
            new_object.pk,
        )
