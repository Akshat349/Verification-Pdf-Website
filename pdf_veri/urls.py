from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'), 
    path('verify-pdf/no-change', views.verify_pdf_no_change, name='verify_pdf_no_change'),
    path('verify-pdf/change', views.verify_pdf_change, name='verify_pdf_change'),
    path('success/', views.success_page, name='success'),

    path('clear-history/', views.clear_history, name='clear_history'),
    
    path('declaration/', views.declaration_view, name='declaration_page'),
    path('reports/', views.report_view, name='report_page'),
]