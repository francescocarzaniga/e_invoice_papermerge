from django.apps import AppConfig


class EInvoiceConfig(AppConfig):
    name = 'papermerge.apps.e_invoice'
    label = 'e_invoice'

#    def ready(self):
#        from papermerge.apps.data_retention import signals  # noqa
