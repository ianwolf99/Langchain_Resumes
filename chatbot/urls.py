# chatbot/urls.py
from django.urls import path
from .views import  chat_view ,login_view, register , upload_resume_view, upload_success_view, login_view, logout_view

urlpatterns = [
    #path('', chat, name='chat'),
    path('', chat_view, name='chat'),
    path('upload/', upload_resume_view, name='upload_resume'),
    path('upload-success/', upload_success_view, name='upload_success'),
    path('login/', login_view, name='login'),
    path('register/', register, name='register'),

    
]
