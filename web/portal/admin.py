from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import *

models_to_register = [Client, ASN, Netblock, IPAddress, Port, Domain, Subdomain]

# Register all models in the admin interface
for model in models_to_register:
    admin.site.register(model, SimpleHistoryAdmin)
