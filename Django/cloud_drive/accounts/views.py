from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.core.files import File
from django.core.serializers.json import DjangoJSONEncoder
import mimetypes
from django.contrib.auth.models import User
from collections import Counter
from django.utils import timezone
import uuid
import os, json, calendar
from django.db.models import Count, Sum
from django.db import transaction
from .models import UploadedFile, Folder
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UploadFileForm, FolderForm, MoveFileForm

# Create your views here.
@login_required
def home(request):
    # Retrieve all users and their folders/files
    users_data = {}
    users = User.objects.exclude(username=request.user.username)

    for user in User.objects.all():
        folders = Folder.objects.filter(user=user)
        files = UploadedFile.objects.filter(user=user)

        users_data[user.username] = {
            'folders': folders,
            'files': files,
            'folder_sizes': {folder.id: get_folder_size(folder) for folder in folders}
        }

    context = {
        'current_user': request.user,
        'other_users': users,
        'users_data': users_data,
    }

    return render(request, 'home.html', context)

@login_required
def main(request):
    print(f'Logged in user: {request.user.username}')
    
    # Get main folders (top-level folders)
    main_folders = Folder.objects.filter(user=request.user, parent_folder__isnull=True)
    
    # Get all folders for the user (not just main folders)
    all_folders = Folder.objects.filter(user=request.user)  # Ensure we only get folders for the logged-in user
    
    # Get user files not in a folder
    user_files = UploadedFile.objects.filter(user=request.user, folder__isnull=True)

    # 1. File Type Distribution
    file_types = [file.file.name.split('.')[-1].lower() for file in user_files]
    file_type_counts = Counter(file_types)

    # Prepare data for file types and counts for chart
    file_type_labels = list(file_type_counts.keys())
    file_type_counts = list(file_type_counts.values())

    # 2. Storage Usage Over Time
    current_year = timezone.now().year
    monthly_usage = []

    for month in range(1, 13):
        month_files = UploadedFile.objects.filter(
            user=request.user,
            uploaded_at__year=current_year,
            uploaded_at__month=month
        )
        total_size = month_files.aggregate(total=Sum('file_size'))['total'] or 0
        monthly_usage.append(total_size / (1024 * 1024))  # Convert to MB

    month_labels = [calendar.month_abbr[m] for m in range(1, 13)]

    # Pass all necessary data to the template context
    context = {
        'user_files': user_files,
        'main_folders': main_folders,
        'all_folders': all_folders,  # You can decide if you want to show all folders or just main folders
        'file_type_labels': file_type_labels,
        'file_type_counts': file_type_counts,
        'month_labels': month_labels,
        'monthly_usage': monthly_usage,
    }

    return render(request, 'main.html', context)

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request,user)
            messages.success(request,f'Welcome {user.username}! Your account has been created!')
            return redirect('main')
        else:
            print(form.errors)
    else:
        form = UserCreationForm()
    return render(request,'signup.html',{'form':form})

from django.contrib.auth import logout as auth_logout

def create_folder(request):
    if request.method == 'POST':
        form = FolderForm(request.POST)
        if form.is_valid():
            new_folder = form.save(commit=False)
            new_folder.user = request.user
            new_folder.save()
            messages.success(request, 'Folder created successfully!')
            return redirect('main')
    else:
        form = FolderForm()
    return render(request, 'create_folder.html',{'form':form})

def get_folder_size(folder):
    total_size = 0
    # Add size of files in the folder
    for file in UploadedFile.objects.filter(folder=folder):
        total_size += file.file_size

    # Recursively add sizes of subfolders
    for subfolder in folder.subfolders.all():
        total_size += get_folder_size(subfolder)

    return total_size

def rename_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id, user=request.user)
    if request.method == 'POST':
        form = FolderForm(request.POST, instance=folder)
        if form.is_valid():
            form.save()
            messages.success(request, 'Folder renamed successfully!')
            return redirect('main')
    else:
        form = FolderForm(instance=folder)
    return render(request, 'rename_folder.html', {'form': form, 'folder': folder})

def view_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id, user=request.user)
    files_in_folder = UploadedFile.objects.filter(folder=folder)
    subfolders = folder.subfolders.all()
    return render(request, 'folder_view.html', {'folder': folder, 'files': files_in_folder, 'subfolders': subfolders})


def move_folder(request, folder_id, target_folder_id=None):
    folder = get_object_or_404(Folder, id=folder_id)
    target_folder = get_object_or_404(Folder, id=target_folder_id) if target_folder_id else None
    
    folder.parent_folder = target_folder  # `None` means it will move to the main menu
    folder.save()
    return redirect('main')  # Adjust the redirect as necessary

@login_required
def preview_file(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    mime_type = mimetypes.guess_type(uploaded_file.file.url)[0]
    
    # Debug output
    print(f"Detected MIME type: {mime_type}")

    absolute_url = request.build_absolute_uri(uploaded_file.file.url)
    context = {
        'uploaded_file': uploaded_file,
        'mime_type': mime_type,
        'is_image': mime_type and mime_type.startswith('image'),
        'is_video': mime_type and mime_type.startswith('video'),
        'is_audio': mime_type and mime_type.startswith('audio'),
        'is_pdf': uploaded_file.file.name.lower().endswith('.pdf'),
        'is_doc': uploaded_file.file.name.lower().endswith(('.doc', '.docx')),
        'is_text': mime_type and mime_type.startswith('text'),
        'absolute_url': absolute_url,
    }
    return render(request, 'preview_file.html', context)

@login_required
def copy_file(request, file_id):
    # Get the original file
    original_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    
    # Create a copy of the file
    original_file_path = original_file.file.path
    file_basename, file_extension = os.path.splitext(original_file.file.name)
    new_file_name = f"{file_basename}_copy_{uuid.uuid4().hex[:6]}{file_extension}"
    file_size = original_file.file.size
    
    # Create a new UploadedFile instance
    with open(original_file_path, 'rb') as file_content:
        new_file_instance = UploadedFile(
            user=request.user,
            file=File(file_content, name=new_file_name),
            file_size=file_size
        )
        new_file_instance.save()

    # Notify user and redirect
    messages.success(request, f"{original_file.file.name} copied successfully as {new_file_name}.")
    return redirect('main')  # Redirect to main page or file listing page

@login_required
def move_file(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)

    if request.method == 'POST':
        form = MoveFileForm(request.POST, user=request.user)
        if form.is_valid():
            new_folder = form.cleaned_data['folder']
            old_folder = uploaded_file.folder  # Reference to the old folder

            # Move the file to the new folder
            uploaded_file.folder = new_folder
            uploaded_file.save()  # Save the changes

            # Update sizes of both folders
            if old_folder:  # Ensure old_folder exists
                old_folder.update_size()  # Update the old folder's size
            new_folder.update_size()  # Update the new folder's size

            messages.success(request, 'File moved successfully!')
            return redirect('main')
    else:
        form = MoveFileForm(user=request.user)

    return render(request, 'move_file.html', {'form': form, 'file': uploaded_file})


@login_required
def move_file_to_main(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    
    if request.method == 'POST':
        # Move the file back to the main page
        uploaded_file.folder = None  # Set folder to None
        uploaded_file.save()  # Save changes
        
        messages.success(request, 'File moved back to the main page successfully!')
        return redirect('main')  # Redirect to your main page
    
    return render(request, 'move_file_to_main.html', {'file': uploaded_file})

def logout(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('login')

@login_required
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.save(commit=False)
            uploaded_file.user = request.user
            uploaded_file.file_size = uploaded_file.file.size
            
            # Check if the individual file size exceeds 40MB
            if uploaded_file.file_size > 41943040:  # 40 MB in bytes
                messages.error(request, 'File size exceeds 40MB. Please upload a smaller file.')
                return redirect('upload_file')

            # Calculate the total size of all uploaded files for the current user
            total_size = sum(file.file_size for file in UploadedFile.objects.filter(user=request.user))
            
            # Check if adding this file would exceed the 100MB limit
            if total_size + uploaded_file.file_size > 100 * 1024 * 1024:  # 100 MB in bytes
                messages.error(request, 'Total file size exceeds 100MB. Please delete some files before uploading new ones.')
                return redirect('upload_file')

            # Save the uploaded file
            uploaded_file.save()
            print(f'File size: {uploaded_file.file_size}')
            messages.success(request, 'File uploaded successfully!')
            return redirect('main')
        else:
            messages.error(request, 'File upload failed. Please correct the errors below.')
    else:
        form = UploadFileForm()
    
    return render(request, 'upload.html', {'form': form})


@login_required
def delete_file(request, file_id):
    file_to_delete = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    file_to_delete.file.delete()  # Remove file from storage
    file_to_delete.delete()       # Remove file record from the database
    messages.success(request, 'File deleted successfully!')
    return redirect('main')

def create_subfolder(request, folder_id):
    if request.method == 'POST':
        folder = get_object_or_404(Folder, id=folder_id, user=request.user)
        subfolder_name = request.POST.get('subfolder_name')
        if subfolder_name:
            Folder.objects.create(name=subfolder_name, parent_folder=folder, user=request.user)
            messages.success(request, "Subfolder created successfully.")
        return redirect('view_folder', folder_id=folder_id)
    
# Move a folder to the main menu (i.e., set its parent folder to None)
def move_to_main_menu(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id, user=request.user)
    folder.parent_folder = None
    folder.save()
    messages.success(request, f"'{folder.name}' has been moved to the main menu.")
    return redirect('main')

# Move a folder into another folder
def move_to_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id, user=request.user)

    # If the request method is POST, process the form
    if request.method == 'POST':
        target_folder_id = request.POST.get('target_folder_id')
        if target_folder_id:
            target_folder = get_object_or_404(Folder, id=target_folder_id, user=request.user)

            # Avoid self-referencing moves
            if folder.id == target_folder.id:
                messages.error(request, "Cannot move a folder into itself.")
                return redirect('view_folder', folder_id=folder_id)

            # Update the folder's parent to the selected target folder and save
            folder.parent_folder = target_folder
            folder.save()
            messages.success(request, f"'{folder.name}' has been moved to '{target_folder.name}'.")
            return redirect('view_folder', folder_id=target_folder.id)
        else:
            messages.error(request, "Please select a target folder.")

    # Exclude the folder itself and all its subfolders from possible move targets
    possible_folders = Folder.objects.filter(user=request.user).exclude(id=folder.id)
    subfolder_ids = folder.get_all_subfolder_ids()  # This method collects IDs for all nested subfolders
    possible_folders = possible_folders.exclude(id__in=subfolder_ids)

    return render(request, 'move_folder.html', {
        'folder': folder,
        'possible_folders': possible_folders
    })

def copy_folder(request, folder_id):
    original_folder = get_object_or_404(Folder, id=folder_id, user=request.user)

    # Recursive function to copy folders and files
    def duplicate_folder(folder, parent=None):
        # Create the new folder
        new_folder = Folder.objects.create(
            name=f"{folder.name} (Copy)",
            user=folder.user,
            parent_folder=parent
        )
        
        # Copy files in this folder
        for file in folder.uploadedfile_set.all():
            UploadedFile.objects.create(
                file=file.file,
                folder=new_folder,
                file_size=file.file_size,
                uploaded_at=file.uploaded_at,
                user=file.user
            )

        # Recursively copy subfolders
        for subfolder in folder.subfolders.all():
            duplicate_folder(subfolder, new_folder)

    # Start copying from the root folder
    duplicate_folder(original_folder)

    return redirect('view_folder', folder_id=original_folder.parent_folder.id if original_folder.parent_folder else None)

@login_required
def delete_subfolder(subfolder):
    """Helper function to delete subfolder contents."""
    for file in subfolder.user.files.filter(folder=subfolder):
        file.file.delete()  # Delete the file from storage
        file.delete()       # Delete the file record from the database
    for nested_subfolder in subfolder.subfolders.all():
        delete_subfolder(nested_subfolder)  # Recursively delete subfolders
    subfolder.delete()  # Delete the subfolder itself

@login_required
def delete_folder(request, folder_id):
    folder_to_delete = get_object_or_404(Folder, id=folder_id, user=request.user)
    # Delete all files in this folder
    for file in folder_to_delete.user.files.filter(folder=folder_to_delete):
        file.file.delete()  # Delete the file from storage
        file.delete()       # Delete the file record from the database  
    # Optionally, delete all subfolders and their contents
    for subfolder in folder_to_delete.subfolders.all():
        delete_subfolder(subfolder) 
    # Delete the folder itself
    folder_to_delete.delete()
    messages.success(request, 'Folder deleted successfully!')
    return redirect('main')

def file_drive_stats(request):
    # Aggregate File Type Distribution
    file_type_counts = (
        UploadedFile.objects.filter(user=request.user)
        .values('file_type')
        .annotate(count=Count('id'))
    )

    # Prepare data for file type chart
    file_types = [entry['file_type'] for entry in file_type_counts]
    file_counts = [entry['count'] for entry in file_type_counts]

    # Aggregate Storage Usage Over Time (e.g., by month)
    storage_usage = (
        UploadedFile.objects.filter(user=request.user)
        .extra({'month': "DATE_TRUNC('month', upload_date)"})
        .values('month')
        .annotate(usage=Sum('file_size'))
    )

    # Prepare data for storage usage chart
    months = [entry['month'].strftime('%Y-%m') for entry in storage_usage]
    usage = [entry['usage'] / (1024 ** 3) for entry in storage_usage]  # Convert bytes to GB

    # Pass data to the template
    return render(request, 'file_drive_stats.html', {
        'file_types': json.dumps(file_types, cls=DjangoJSONEncoder),
        'file_counts': json.dumps(file_counts, cls=DjangoJSONEncoder),
        'months': json.dumps(months, cls=DjangoJSONEncoder),
        'usage': json.dumps(usage, cls=DjangoJSONEncoder),
    })