from django.urls import path
from.views import *


urlpatterns = [
    path('home/', home, name='policy'),
    path('policy/', policy_compliance_view , name='policy'),
    ]