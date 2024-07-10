# chatbot/urls.py
from django.urls import path
from .views import  chat_view 

urlpatterns = [
    #path('', chat, name='chat'),
    path('', chat_view, name='chat'),
    
]
