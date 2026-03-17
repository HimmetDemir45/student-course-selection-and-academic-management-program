from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from core.permissions import role_required


@login_required
@role_required("admin")
def index(request):
    return HttpResponse("Admin dashboard protected page")
