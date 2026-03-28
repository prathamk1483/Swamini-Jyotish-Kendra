from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('',views.index,),
    path('delete/<str:record_id>/', views.api_delete_kundali, name='api_delete_kundali'),
    path('editor/', views.kundali_editor, name='new_kundali'),
    path('editor/<str:record_id>/', views.kundali_editor, name='edit_kundali'),
    path('api/save/', views.api_save_kundali, name='api_save_kundali'),
    path('api/load/<str:record_id>/', views.api_load_kundali, name='api_load_kundali'),
    path('api/loadAll/', views.api_load_all, name='api_load_all'), # <--- NEW ENDPOINT
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
