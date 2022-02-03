from typing import Dict, List
from webbrowser import get

from django.apps import apps
from django.db.models.fields.reverse_related import ManyToManyRel, ManyToOneRel
from django.forms import models

from automatic_crud.data_types import Instance, DjangoForm


def get_model(__app_name: str, __model_name: str) -> Instance:
    # return the model corresponding to the application name and model name sent
    return apps.get_model(app_label=__app_name, model_name=__model_name)


def get_object(model: Instance, id: int):
    # return the record for a id sended
    instance = model.objects.filter(id=id, model_state=True).first()
    if instance:
        return instance
    return None


def get_model_fields_names(__model: Instance) -> List:
    # return a list of field names from a model
    return [name for name, _ in models.fields_for_model(__model).items()]


def get_queryset(__model: Instance) -> Dict:
    # returns all records in a dictionary for a model
    return __model.objects.all().values()


def get_form(form: DjangoForm, model: Instance) -> DjangoForm:
    """
    Return a Django Form for a model, also a Django Form can be indicated
    by default the Django Form will exclude the 'state' field from the model
    """
    if form is not None:
        return models.modelform_factory(model=model, form=form)
    else:
        return models.modelform_factory(model=model, exclude=('model_state',))


def build_template_name(template_name: str, model: Instance, action: str) -> str:
    """
    Build template name with app label from model, model name and action(list,create,update,detail)
    """
    if template_name == None:
        template_name = '{0}/{1}_{2}.html'.format(
            model._meta.app_label,
            model._meta.object_name.lower(),
            action
        )
    return template_name


def normalize_model_structure(model, instance) -> dict:
    """
    Turn models instances into plain dictionaries to be returned in responses
    """
    from automatic_crud.models import BaseModel
    if issubclass(model, BaseModel):
        model: BaseModel = model


    normalized_instance = {
        'id': instance['id'] if 'id' in instance.keys() else instance['pk']
    }
    
    excluded = model.exclude_fields + ['id'] 
    # Fallback
    for f in model._meta.get_fields():
        if isinstance(f, ManyToManyRel) or isinstance(f, ManyToOneRel) or f.name in excluded or f.name not in instance['fields'].keys():
            continue
        normalized_instance[f.name] = instance['fields'][f.name]

    return normalized_instance

