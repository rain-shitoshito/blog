from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.Top.as_view(), name='top'),
    path('detail/<int:pk>', views.Detail.as_view(), name='detail'),
    path('admin/', views.Admin.as_view(), name='admin'),
    path('admin/tag-register/', views.Tag.as_view(), name='tag_register'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.authview.LogoutView.as_view(), name='logout'),
]
