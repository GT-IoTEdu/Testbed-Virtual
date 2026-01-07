from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader

# Create your views here.

@login_required
def users(request):
    template = loader.get_template('base/users.html')
    meta = request.META
    return HttpResponse(template.render(meta, request))
