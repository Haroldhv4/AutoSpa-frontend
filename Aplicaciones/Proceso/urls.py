from django.urls import path
from . import views
urlpatterns=[
    path('', views.plantilla),
    path("plantilla/",views.plantilla,name="plantilla"),
    path("login/", views.login_view, name="login"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("check-session/", views.check_session_view, name="check-session"),
    path('logout/', views.logout_view, name='logout'),
]