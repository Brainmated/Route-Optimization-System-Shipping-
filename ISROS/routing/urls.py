from django.urls import path, re_path
from . import views
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.base import RedirectView

urlpatterns = [
    # Redirect the base URL to /debug/
    path('', RedirectView.as_view(url='/debug/', permanent=False), name='index'),

    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='index'), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('map/', views.show_map, name='map'),
    path('debug/', views.debug_view, name='debug'),
    # Add other paths as needed
]