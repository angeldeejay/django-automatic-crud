import json
import ast
import re

from django.db.models.fields import *
from django.http import HttpResponse, JsonResponse as JSR
from django.core.serializers import serialize
from django.core.paginator import Paginator

from automatic_crud.generics import BaseCrud
from automatic_crud.utils import get_object, get_form, normalize_model_structure
from automatic_crud.response_messages import *


class BaseCrudAJAX(BaseCrud):
    form_class = None

    def _get_invalid_request_response(self):
        """
        Validate the current request and ensure if need authentication and
        permissions

        """
        validations = [
            # login required validation
            self.validate_login_required,
            # permission required validation
            self.validate_permissions
        ]

        for validation in validations:
            validation_required, validation_response = validation()
            if validation_required:
                return validation_response

        return None

    def _normalize_data(self, is_list=False):
        """
        Generate an HttpResponse instance to get the serialized query and
        delete the ['model'] key from the dictionary and convert the dictionary
        to json and save on self.data

        """
        temp_response = JSR({'data': self.data})
        temp_data = temp_response.content.decode("UTF-8")
        temp_data = ast.literal_eval(temp_data)
        temp_data = json.loads(temp_data['data'])
        object_list: list = []
        for instance in temp_data:
            instance = normalize_model_structure(self.model, instance)
            object_list.append(instance)
        self.data = json.dumps(object_list if is_list else object_list.pop())

    def _get_query_string(self):
        """
        Generate a dictionary with query string matching model fields

        """
        received_query_dict = self.request.GET.dict()
        valid_query_dict = {}

        query_keys = list(received_query_dict.keys())
        model_fields = self.model._meta.fields
        model_fields_names = [f.name for f in model_fields]
        for f in model_fields:
            regex = f'^(?P<field_name>{f.name})(?P<field_outer_name>__(_?[a-zA-Z0-9])+)?(?P<mutator>__i(startswith|endswith|contains|n))?$'
            filter_alias = None
            filter_expanded = None
            for q in query_keys:
                if re.sub(regex, '\\1', q) == f.name:
                    m = re.match(regex, q)
                    filter_expanded = {}
                    for k in ['field_name', 'field_outer_name', 'mutator']:
                        filter_expanded[k] = m.group(k)
                    filter_alias = q
                    break

            if filter_alias is None:
                continue

            if isinstance(f, BooleanField):
                valid_query_dict[filter_alias] = str(
                    received_query_dict[filter_alias]).lower() == 'true'
            else:
                if filter_expanded is None:
                    valid_query_dict[filter_alias] = received_query_dict[filter_alias]
                else:
                    if filter_expanded['mutator'] == '__in':
                        valid_query_dict[filter_alias] = [
                            v.strip() for v in received_query_dict[filter_alias].split(',')]
                    else:
                        valid_query_dict[filter_alias] = received_query_dict[filter_alias]

        if 'model_state' not in valid_query_dict.keys() and 'model_state' in model_fields_names:
            valid_query_dict['model_state'] = True

        return valid_query_dict


class BaseListAJAX(BaseCrudAJAX):
    def get_queryset(self):
        """
        Returns the values as a dictionary ordered by the order_by attribute,
        by default order_by = id

        """
        filters = self._get_query_string()

        queryset = self.model.objects\
            .filter(**filters)\
            .select_related(*self.model.preloads)\
            .prefetch_related(*self.model.preloads)\
            .order_by(f"{self.request.GET.get('order_by','id')}")

        return queryset

    def get(self, request, model, *args, **kwargs):
        """
        Return data of model

        The follow attributes can be sent in request.GET:
            paginate: results should be paginated
            offset: element number where the page starts
            limit: number of record to resolve

        The response structure when results are being paginated is:

            {
                'length': # amount of records in resultset,
                'objects': # list of records in current page
            }

        In the other case, a plain list will be returned:

            [
                ... # list of all records
            ]

        """
        self.model = model

        invalid_request_response = self._get_invalid_request_response()
        if invalid_request_response is not None:
            return invalid_request_response

        self.data = serialize('entity_json', self.get_queryset(),
                              fields=self.get_fields_for_model() + self.model.preloads,
                              use_natural_foreign_keys=True)

        if 'paginate' in self.request.GET:
            limit = int(self.request.GET.get('limit', '10'))
            offset = int(self.request.GET.get('offset', '0'))
            paginator = Paginator(self.get_queryset(), limit)
            self.data = serialize('entity_json', paginator.get_page((offset / limit) + 1),
                                  fields=self.get_fields_for_model() + self.model.preloads,
                                  use_natural_foreign_keys=True)
            self._normalize_data(is_list=True)
            self.data = json.dumps({
                'length': self.get_queryset().count(),
                'objects': json.loads(self.data)
            })
        else:
            self.data = serialize('entity_json', self.get_queryset(),
                                  fields=self.get_fields_for_model() + self.model.preloads,
                                  use_natural_foreign_keys=True)
            self._normalize_data(is_list=True)

        return HttpResponse(self.data, content_type="application/json")


class BaseCreateAJAX(BaseCrudAJAX):
    def post(self, request, model, form=None, *args, **kwargs):
        self.model = model

        invalid_request_response = self._get_invalid_request_response()
        if invalid_request_response is not None:
            return invalid_request_response

        self.form_class = get_form(form, self.model)
        form = self.form_class(json.loads(request.body), request.FILES)
        if form.is_valid():
            instance = form.save()
            self.data = serialize(
                'entity_json', [instance, ],
                fields=self.get_fields_for_model(),
                use_natural_foreign_keys=True
            ) if instance is not None and instance.id is not None else None
            self._normalize_data()
            return success_create_message(self.model, self.data)
        return error_create_message(self.model, form)


class BaseDetailAJAX(BaseCrudAJAX):
    def get(self, request, model, *args, **kwargs):
        self.model = model

        invalid_request_response = self._get_invalid_request_response()
        if invalid_request_response is not None:
            return invalid_request_response

        instance = get_object(self.model, self.kwargs['id'])
        if instance is not None:
            self.data = serialize(
                'entity_json', [instance, ],
                fields=self.get_fields_for_model(),
                use_natural_foreign_keys=True
            )
            self._normalize_data()
            return HttpResponse(self.data, content_type="application/json")
        return not_found_message(self.model)


class BaseUpdateAJAX(BaseCrudAJAX):
    def put(self, request, model, form=None, *args, **kwargs):
        self.model = model

        invalid_request_response = self._get_invalid_request_response()
        if invalid_request_response is not None:
            return invalid_request_response

        self.form_class = get_form(form, self.model)
        instance = get_object(self.model, self.kwargs['id'])
        if instance is not None:
            form = self.form_class(
                json.loads(request.body), request.FILES, instance=instance)
            if form.is_valid():
                instance = form.save()
                self.data = serialize(
                    'entity_json', [instance, ],
                    fields=self.get_fields_for_model(),
                    use_natural_foreign_keys=True
                ) if instance is not None and instance.id is not None else None
                self._normalize_data()
                return success_update_message(self.model, self.data)
            else:
                return error_update_message(self.model, form)
        return not_found_message(self.model)


class BaseRestoreAJAX(BaseCrudAJAX):
    def put(self, request, model, form=None, *args, **kwargs):
        self.model = model

        invalid_request_response = self._get_invalid_request_response()
        if invalid_request_response is not None:
            return invalid_request_response

        instance = get_object(self.model, self.kwargs['id'], force=True)
        if instance is not None:
            instance.model_state = True
            instance.save(force_update=True)
            self.data = serialize(
                'entity_json', [instance, ],
                fields=self.get_fields_for_model(),
                use_natural_foreign_keys=True
            ) if instance is not None and instance.id is not None else None
            self._normalize_data()
            return success_update_message(self.model, self.data)
        return not_found_message(self.model)


class BaseDeleteAJAX(BaseCrudAJAX):
    def delete(self, request, model, *args, **kwargs):
        self.model = model

        invalid_request_response = self._get_invalid_request_response()
        if invalid_request_response is not None:
            return invalid_request_response

        instance = get_object(self.model, self.kwargs['id'], force=True)
        if instance is not None:
            instance.delete()
            instance.id = self.kwargs['id']
            self.data = serialize(
                'entity_json', [instance, ],
                fields=self.get_fields_for_model(),
                use_natural_foreign_keys=True
            )
            self._normalize_data()
            return success_delete_message(self.model, self.data)
        return not_found_message(self.model)


class BaseSoftDeleteAJAX(BaseCrudAJAX):
    def delete(self, request, model, *args, **kwargs):
        self.model = model

        invalid_request_response = self._get_invalid_request_response()
        if invalid_request_response is not None:
            return invalid_request_response

        instance = get_object(self.model, self.kwargs['id'])
        if instance is not None:
            instance.model_state = False
            instance.save(force_update=True)
            self.data = serialize(
                'entity_json', [instance, ],
                fields=self.get_fields_for_model(),
                use_natural_foreign_keys=True
            )
            self._normalize_data()
            return success_delete_message(self.model, self.data)
        return not_found_message(self.model)
