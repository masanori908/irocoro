from django.urls import path
from django.contrib.auth import views as auth_views
from .views import SignupView
from . import views
from django.conf import settings
from django.conf.urls.static import static


app_name = 'careapp'

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/",auth_views.LoginView.as_view(template_name="login.html"),name="login"),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('',views.IndexView.as_view(),name='index'),
    path('endlog/',views.EndLogView.as_view(),name='endlog'),
    path('result/',views.ResultView.as_view(),name='result'),
    path("calendar/", views.CalendarView.as_view(), name="calendar"),
    path("history/<int:year>/<int:month>/<int:day>/", views.HistoryDetailView.as_view(), name="history_detail"),
    path('graph/',views.GraphView.as_view(),name='graph'),
    path("log/<int:year>/<int:month>/<int:day>/", views.PastLogView.as_view(), name="past_log"),
]

# 画像アップロードのためのルーティング
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
