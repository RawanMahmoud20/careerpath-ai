from django.shortcuts import render


def landing(request):
    """Public landing page with links to login and register."""
    return render(request, "core/landing.html")
