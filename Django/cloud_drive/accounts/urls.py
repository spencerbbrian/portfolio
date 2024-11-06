from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
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
    path('copy-file/<int:file_id>/', views.copy_file, name='copy_file'),
    path('move-folder/<int:folder_id>/', views.move_folder, name='move_folder'),
    path('move-folder/<int:folder_id>/<int:target_folder_id>/', views.move_folder, name='move_folder'),
    path('folder/<int:folder_id>/', views.view_folder, name='view_folder'),
    path('folder/<int:folder_id>/create-subfolder/', views.create_subfolder, name='create_subfolder'),
    path('folder/<int:folder_id>/move-to-main/', views.move_to_main_menu, name='move_to_main_menu'),
    path('folder/<int:folder_id>/move-to-folder/', views.move_to_folder, name='move_to_folder'),
    path('copy-folder/<int:folder_id>/', views.copy_folder, name='copy_folder'),
    path('home/', views.home, name='home'),
    path('file-drive-stats/', views.file_drive_stats, name='file_drive_stats'),
    path('profile/', views.profile, name='profile'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)