from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm
from .pathing import Pathing, GridMap
from django.contrib.auth.views import LoginView, LogoutView
from .utils import get_ports_from_csv
import folium

# Home page view
def index(request):
    return render(request, 'index.html')

# Login view
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user:
                login(request, user)
                return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# Logout view
def logout_view(request):
    logout(request)
    return render(request, 'logout.html')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            # You can then redirect to the login page, for example
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def show_map(request):
    min_x, min_y = (30.0, -120.0)
    max_x, max_y = (50.0, -70.0) 
    # Check if the form has been submitted
    csv_filepath = 'E:/Programming in Python/applications/Thesis/ISROS/routing/data/ports.csv'
    ports = get_ports_from_csv(csv_filepath)
    grid_map = GridMap(bounds=((min_x, min_y), (max_x, max_y)), resolution=5)

    if request.method == 'POST':
        # Get locations from the POST request
        location1 = [float(coord) for coord in request.POST['location1'].split(',')]
        location2 = [float(coord) for coord in request.POST['location2'].split(',')]

        # Create a Pathing instance and generate the map
        path = Pathing(location1, location2, grid_map)
        folium_map = path.get_map()
    else:
        # Default map centered at an initial location
        folium_map = folium.Map(location=[45.5236, -122.6750], zoom_start=5)

    # Pass the map to the template
    map_html = folium_map._repr_html_()
    context = {
        'map': map_html,
        'ports': ports,
    }
    return render(request, 'map.html', context)