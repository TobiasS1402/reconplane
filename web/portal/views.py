from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from celery import chain
from .tasks import *
from .models import *


@login_required
def dashboard(request):
    domains = Domain.objects.all()  # Fetch all domains from the database
    subdomains = Subdomain.objects.all() 

    subdomains_dict = {}

    for domain in domains:
        subdomain = Subdomain.objects.filter(domain=domain)
        subdomains_dict[domain] = subdomain
    return render(request, 'domains.html', {'domains':domains, 'subdomains':subdomains, 'subdomains_dict':subdomains_dict})

@login_required
def trigger_task(request):
    if request.method == 'POST':
        #trigger_generic_task
        domain = request.POST.get('domain_name')
        print(domain)
        chain(subdomainSubfinder.s(domain), subdomains_processing.s(domain))()
        return HttpResponseRedirect(reverse('index'))
    else:
        return HttpResponseRedirect(reverse('index'))
