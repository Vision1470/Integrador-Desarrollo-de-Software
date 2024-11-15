from django.shortcuts import render
from django.shortcuts import HttpResponse
from django.http import JsonResponse
from .models import area, actividad
from django.shortcuts import get_object_or_404

# Create your views here.
     
def Area(request):
   #areas = list(area.objects.values())
    Areas = area.objects.all()
    return render(request, 'area.html', {
        'areas' : Areas
    })

def Actividad(request):
    #actividades = get_object_or_404(actividad, id=id)
    Actividades = actividad.objects.all()
    return render(request, 'actividad.html', {
        'actividades' : Actividades 
    })







''''
def hola(request, usuario):
    return HttpResponse("Hola: %s" %usuario)
'''


'''
def index(request):
    title = "welcome"
    return render (request, "index.html", {
        'title': title
    })

def sobre(request):
    username = 'yo'
    return render(request, 'sobre.html', {
        'username': username
    })
'''