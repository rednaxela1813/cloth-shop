from django.apps import AppConfig


class CsmConfig(AppConfig):
    djfault_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.csm'
    label = 'csm'
