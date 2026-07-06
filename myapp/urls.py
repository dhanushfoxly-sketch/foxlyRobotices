from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('categories/', views.categories, name='categories'),
    path('products/', views.products, name='products'),
    path('projects/<int:project_id>/request-code/', views.request_download, name='request_download'),
    path('projects/<int:project_id>/verify-code/', views.verify_download, name='verify_download'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
