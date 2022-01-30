from automatic_crud.data_types import Instance, JsonResponse, DjangoForm
from django.core.serializers import serialize
from django.http import JsonResponse as JSR
from django.http import JsonResponse as JR
from django.utils.translation import gettext as _
import ast
import json

def jr_response(message: str, error: str, status_code: int, data: str = None) -> JsonResponse:
    response = JR({
        'message': message,
        'error': error,
        'object': json.loads(data) if data is not None else None
    })
    response.status_code = status_code
    return response


def success_create_message(model: Instance, data: dict = None) -> JsonResponse:
    message = model().build_message(model.success_create_message)
    error = None
    return jr_response(message, error, 201, data)


def error_create_message(model: Instance, form: DjangoForm) -> JsonResponse:
    message = model().build_message(model.error_create_message)
    error = form.errors
    return jr_response(message, error, 400, None)


def success_update_message(model: Instance, data: dict = None) -> JsonResponse:
    message = model().build_message(model.success_update_message)
    error = None
    return jr_response(message, error, 200, data)


def error_update_message(model: Instance, form: DjangoForm) -> JsonResponse:
    message = model().build_message(model.error_update_message)
    error = form.errors
    return jr_response(message, error, 400, None)


def success_delete_message(model: Instance, data: dict = None) -> JsonResponse:
    message = model().build_message(model.success_delete_message)
    error = None
    return jr_response(message, error, 200, data)


def not_found_message(model: Instance) -> JsonResponse:
    print(model.not_found_message)
    print(_(model.not_found_message))
    response = JR({'error': _(model.not_found_message)})
    response.status_code = 400
    return response
