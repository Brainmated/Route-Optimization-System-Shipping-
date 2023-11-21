import requests
import datetime
from django.shortcuts import render


# Create your views here.
def index(request):
    API_KEY = open("API_KEY", "r").read()