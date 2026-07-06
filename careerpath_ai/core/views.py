from django.shortcuts import render

from careers.models import Career


def landing(request):
    """Public landing page with links to login and register."""
    careers = Career.objects.all().order_by('title')
    return render(request, "landing.html", {"careers": careers})
