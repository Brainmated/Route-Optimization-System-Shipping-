from django.urls import path
from . import views
from .views import index, login_view, logout_view, show_map
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('', index, name='index'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='index'), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('map/', show_map, name='map'),
    # Add other paths as needed
]