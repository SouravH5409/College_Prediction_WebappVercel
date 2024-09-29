from django.urls import path
from .views import (home_view, user_input_view, results_view, signup_view, login_view, logout_view)
#from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', home_view, name='home'),            
    path('login/', login_view, name='login'),    
    path('signup/', signup_view, name='signup'), 
    path('predict/', user_input_view, name='predict_form'),  
    path('results/', results_view, name='results'),         
    path('logout/', logout_view, name='logout'),            
]
