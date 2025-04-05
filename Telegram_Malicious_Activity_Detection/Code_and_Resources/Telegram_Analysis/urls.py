from django.urls import path
from . import views
from .views import send_report

urlpatterns = [
    path('', views.message_form, name='telegramAnalysis'),
    path('chart/', views.chart, name='chart'),
path("send_report/", send_report, name="send_report"),
    # path('download/<str:filename>/', views.download_json, name='download_json'),
]





# analyzer/urls.py
# from django.urls import path
# from . import views
#
# urlpatterns = [
#     path('', views.index, name='index'),
#     path('analyze/', views.analyze, name='analyze'),
# ]
