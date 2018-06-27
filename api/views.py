from django.shortcuts import render

# Create your views here.
from django.shortcuts import render,HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def server(request):
    if request.method == "GET":
        return HttpResponse("GET")
    elif request.method == "POST":
        server_dict = json.loads(request.body.decode('utf-8'))
        print(server_dict)
        return HttpResponse("===>",server_dict)