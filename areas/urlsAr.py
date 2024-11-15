from django.urls import path
from . import views

urlpatterns = [
    #path('', views.index),
    #path('sobre/', views.sobre),
    #path('hola/<str:usuario>', views.hola),
    path('area/', views.Area), 
    path('actividad/', views.Actividad),
]
