from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name="login.html"), name='login'),
    path('logout/',auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('main/', views.main, name='main'),
    path('upload/', views.upload_file, name='upload_file'),
    path('delete-file/<int:file_id>/', views.delete_file, name='delete_file'),
    path('', views.main, name='main'),
    path('create-folder/', views.create_folder, name='create_folder'),
    path('folder/<int:folder_id>/', views.view_folder, name='view_folder'),
    path('rename-folder/<int:folder_id>/', views.rename_folder, name='rename_folder'),
    path('move-file/<int:file_id>/', views.move_file, name='move_file'),
    path('delete-folder/<int:folder_id>/', views.delete_folder, name='delete_folder'),
    path('move-to-main/<int:file_id>/', views.move_file_to_main, name='move_file_to_main'),
    path('preview-file/<int:file_id>/', views.preview_file, name='preview_file'),

]