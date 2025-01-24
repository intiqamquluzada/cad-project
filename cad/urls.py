from django.urls import path
from cad.views import index_view
urlpatterns = [
    path("home/", index_view, name='home'),
]