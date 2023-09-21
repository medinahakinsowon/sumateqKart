from django.urls import path
from . import views


urlpatterns = [
    path('register/', views.register, name="register"),
    path('login/', views.login, name="login"),
    path('logout/', views.logout, name="logout"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('', views.dashboard, name="dashboard"),
    
    path('activate/<uidb64>/<token>/', views.activate, name="activate"),
    path('forgotPassword/', views.forgotPassword, name="forgotPassword"),
    path('passwordreset_validate/<uidb64>/<token>/', views.passwordreset_validate, name="passwordreset_validate"),
    path('resetPassword/', views.resetPassword, name="resetPassword"),
]


# //the empty dashboard is to set the dashboard as the default page when a user loogged in//