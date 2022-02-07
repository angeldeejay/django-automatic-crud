from django.db import models
from django.urls import path, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db.models.fields.related import ForeignKey
from django.db.models.fields.reverse_related import ManyToManyRel, ManyToOneRel
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now

from automatic_crud.utils import get_model
from automatic_crud.data_types import *
from automatic_crud.base_report import GetExcelReport
from automatic_crud.views_crud import *
from automatic_crud.views_crud_ajax import *


class BaseModel(models.Model):
    """Model definition for BaseModel."""

    # TODO: Define fields here
    id = models.AutoField(primary_key=True)
    model_state = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(
        auto_now=True, auto_now_add=False, null=True, blank=True)
    deleted_at = models.DateTimeField(
        auto_now=False, auto_now_add=False, null=True, blank=True)

    create_form = None
    update_form = None

    all_cruds_types = False
    ajax_cruds = False
    normal_cruds = False

    exclude_model = False
    normal_pagination = False
    values_for_page = 10

    login_required = False
    permission_required = ()
    model_permissions = False
    default_permissions = False

    exclude_fields = ['model_state']
    preloads = []

    success_create_message = _('SUCCESS_CREATE_MESSAGE')
    success_update_message = _('SUCCESS_UPDATE_MESSAGE')
    success_delete_message = _('SUCCESS_DELETE_MESSAGE')

    error_create_message = _('ERROR_CREATE_MESSAGE')
    error_update_message = _('ERROR_UPDATE_MESSAGE')
    not_found_message = _('NOT_FOUND_MESSAGE')

    create_template = None
    update_template = None
    list_template = None
    detail_template = None

    class Meta:
        """Meta definition for BaseModel."""
        abstract = True

    def natural_key(self, stop=False) -> dict:
        output = {'id': self.id}
        for f in self.__class__._meta.get_fields():
            # Reverse relationships
            if isinstance(f, ManyToManyRel) or isinstance(f, ManyToOneRel):
                continue
            # Direct relationships
            elif isinstance(f, ForeignKey):
                output[f.name] = getattr(self, f.attname)
            # Model fields
            else:
                output[f.name] = getattr(self, f.name)
        return output

    @staticmethod
    @receiver(pre_save)
    def pre_save(sender, instance, **kwargs):
        instance.deleted_at = None if instance.model_state else now()

    def get_create_form(self, form=None):
        if form != None:
            self.create_form = form
        return self.create_form

    def get_update_form(self, form=None):
        if form != None:
            self.update_form = form
        return self.update_form

    def build_message(self, message: str, custom_message=False):
        if custom_message:
            return "{0}".format(message)
        return "{0} {1}".format(self._meta.verbose_name, _(message))

    def get_create_url(self):
        return "{0}/create/".format(self._meta.object_name.lower())

    def get_list_url(self):
        return "{0}/list/".format(self._meta.object_name.lower())

    def get_restore_url(self):
        return "{0}/restore/<int:id>/".format(self._meta.object_name.lower())

    def get_direct_delete_url(self):
        return "{0}/delete/<int:id>/".format(self._meta.object_name.lower())

    def get_logic_delete_url(self):
        return "{0}/soft-delete/<int:id>/".format(self._meta.object_name.lower())

    def get_update_url(self):
        return "{0}/update/<int:id>/".format(self._meta.object_name.lower())

    def get_detail_url(self):
        return "{0}/detail/<int:id>/".format(self._meta.object_name.lower())

    def get_excel_report_url(self):
        return "{0}/report/".format(self._meta.object_name.lower())

    def get_alias_create_url(self):
        return "{0}-{1}-create".format(self._meta.app_label, self._meta.object_name.lower())

    def get_alias_list_url(self):
        return "{0}-{1}-list".format(self._meta.app_label, self._meta.object_name.lower())

    def get_alias_logic_delete_url(self):
        return "{0}-{1}-soft-delete".format(self._meta.app_label, self._meta.object_name.lower())

    def get_alias_restore_url(self):
        return "{0}-{1}-restore".format(self._meta.app_label, self._meta.object_name.lower())

    def get_alias_direct_delete_url(self):
        return "{0}-{1}-delete".format(self._meta.app_label, self._meta.object_name.lower())

    def get_alias_update_url(self):
        return "{0}-{1}-update".format(self._meta.app_label, self._meta.object_name.lower())

    def get_alias_detail_url(self):
        return "{0}-{1}-detail".format(self._meta.app_label, self._meta.object_name.lower())

    def get_alias_excel_report_url(self):
        return "{0}-{1}-report".format(self._meta.app_label, self._meta.object_name.lower())

    def build_generics_urls(self) -> URLList:
        crud_options_count = [
            self.all_cruds_types,
            self.ajax_cruds,
            self.normal_cruds
        ].count(True)

        if (crud_options_count > 1):
            message = "'{}' should specify only one of these as True: 'all_cruds_types', 'ajax_cruds', 'normal_cruds'".format(
                type(self).__name__)
            raise AttributeError(message)

        urlpatterns = []
        if self.all_cruds_types:
            urlpatterns += self.build_generics_urls_crud()
            urlpatterns += self.build_generics_urls_ajax_crud()
        elif self.ajax_cruds:
            urlpatterns += self.build_generics_urls_ajax_crud()
        elif self.normal_cruds:
            urlpatterns += self.build_generics_urls_crud()

        return urlpatterns

    def build_generics_urls_crud(self) -> URLList:
        __app_name = self._meta.app_label
        __model_name = self._meta.object_name
        __model = get_model(__app_name, __model_name)
        __create_form = self.get_create_form()
        __update_form = self.get_update_form()

        urlpatterns = [
            path(
                "{0}/{1}".format(__app_name, self.get_list_url()),
                BaseList.as_view(
                    template_name=__model.list_template,
                    model=__model
                ),
                name=self.get_alias_list_url()
            ),
            path(
                "{0}/{1}".format(__app_name, self.get_create_url()),
                BaseCreate.as_view(
                    template_name=__model.create_template, model=__model,
                    form_class=__create_form, success_url=reverse_lazy(
                        "{0}".format(self.get_alias_list_url()))
                ),
                name=self.get_alias_create_url()
            ),
            path(
                "{0}/{1}".format(__app_name, self.get_detail_url()),
                BaseDetail.as_view(model=__model),
                name=self.get_alias_detail_url()
            ),
            path(
                "{0}/{1}".format(__app_name, self.get_update_url()),
                BaseUpdate.as_view(
                    template_name=__model.update_template, model=__model,
                    form_class=__update_form, success_url=reverse_lazy(
                        "{0}".format(self.get_alias_list_url()))
                ),
                name=self.get_alias_update_url()
            ),
            path(
                "{0}/{1}".format(__app_name, self.get_logic_delete_url()),
                BaseLogicDelete.as_view(
                    model=__model,
                    success_url=reverse_lazy(
                        "{0}".format(self.get_alias_list_url()))
                ),
                name=self.get_alias_logic_delete_url()
            ),
            path(
                "{0}/{1}".format(__app_name, self.get_direct_delete_url()),
                BaseDirectDelete.as_view(
                    model=__model,
                    success_url=reverse_lazy(
                        "{0}".format(self.get_alias_list_url()))
                ),
                name=self.get_alias_direct_delete_url()
            ),
            path(
                "{0}/{1}".format(__app_name, self.get_excel_report_url()),
                GetExcelReport.as_view(), {
                    '_app_name': __app_name, '_model_name': __model_name},
                name=self.get_alias_excel_report_url()
            ),
        ]

        return urlpatterns

    def build_generics_urls_ajax_crud(self) -> URLList:
        __app_name = self._meta.app_label
        __model_name = self._meta.object_name
        __model = get_model(__app_name, __model_name)
        __model_context = {
            'model': __model
        }
        __model_create_form_context = {
            'model': __model,
            'form': self.get_create_form()
        }
        __model_update_form_context = {
            'model': __model,
            'form': self.get_update_form()
        }
        __prefix = "ajax-" if self.all_cruds_types else ""
        __suffix = "-ajax" if self.all_cruds_types else ""

        urlpatterns = [
            path(
                "{0}{1}/{2}".format(__prefix, __app_name, self.get_list_url()),
                BaseListAJAX.as_view(), __model_context,
                name="{0}{1}".format(self.get_alias_list_url(), __suffix)
            ),
            path(
                "{0}{1}/{2}".format(__prefix, __app_name,
                                    self.get_create_url()),
                BaseCreateAJAX.as_view(), __model_create_form_context,
                name="{0}{1}".format(self.get_alias_create_url(), __suffix)
            ),
            path(
                "{0}{1}/{2}".format(__prefix, __app_name,
                                    self.get_detail_url()),
                BaseDetailAJAX.as_view(), __model_context,
                name="{0}{1}".format(self.get_alias_detail_url(), __suffix)
            ),
            path(
                "{0}{1}/{2}".format(__prefix, __app_name,
                                    self.get_update_url()),
                BaseUpdateAJAX.as_view(), __model_update_form_context,
                name="{0}{1}".format(self.get_alias_update_url(), __suffix)
            ),
            path(
                "{0}{1}/{2}".format(__prefix, __app_name,
                                    self.get_logic_delete_url()),
                BaseSoftDeleteAJAX.as_view(), __model_context,
                name="{0}{1}".format(
                    self.get_alias_logic_delete_url(), __suffix)
            ),
            path(
                "{0}{1}/{2}".format(__prefix, __app_name,
                                    self.get_direct_delete_url()),
                BaseDeleteAJAX.as_view(), __model_context,
                name="{0}{1}".format(
                    self.get_alias_direct_delete_url(), __suffix)
            ),
            path(
                "{0}{1}/{2}".format(__prefix, __app_name,
                                    self.get_restore_url()),
                BaseRestoreAJAX.as_view(), __model_context,
                name="{0}{1}".format(
                    self.get_alias_restore_url(), __suffix)
            ),
            path(
                "{0}{1}/{2}".format(__prefix, __app_name,
                                    self.get_excel_report_url()),
                GetExcelReport.as_view(), {
                    '_app_name': __app_name, '_model_name': __model_name},
                name="{0}{1}".format(
                    self.get_alias_excel_report_url(), __suffix)
            ),
        ]

        return urlpatterns
