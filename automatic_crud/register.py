from django.apps import apps

from automatic_crud.models import BaseModel


def register_models():
    """
    Register models with automatic cruds excluding models with exclude_model = True
    Return urlspatterns with automatic cruds
    """

    urlpatterns = []
    exclude_models = ['ContentType', 'LogEntry',
                      'Session', 'Permission', 'Group']
    models = apps.get_models()

    for model in models:
        if issubclass(model, BaseModel):
            try:
                if model.__name__ not in exclude_models and not model.exclude_model:
                    urlpatterns += model().build_generics_urls()
            except AttributeError:
                raise
            except:
                pass

    return urlpatterns
