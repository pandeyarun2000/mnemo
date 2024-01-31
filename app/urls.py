from django.urls import path
from . import views
from django.contrib import admin
from django.urls import path
from .views import home, process_pdf, download_csv





urlpatterns = [
    path('', home, name='home'),
    path('process_pdf/', process_pdf, name='process_pdf'),
    path('download_csv/', download_csv, name='download_csv'),
    path('admin/', admin.site.urls),
    

]