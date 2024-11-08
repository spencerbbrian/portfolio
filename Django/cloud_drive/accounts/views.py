from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout as auth_logout
from django.core.files import File
import mimetypes
from django.contrib.auth.models import User
from collections import Counter
from django.utils import timezone
import uuid
import mimetypes
import nbformat
from pdf2image import convert_from_path
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import HtmlLexer, CssLexer, PythonLexer, TextLexer
from django.shortcuts import render, get_object_or_404
from .models import UploadedFile
import os, json, calendar
from django.conf import settings
from django.db.models import Sum
from .models import UploadedFile, Folder
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UploadFileForm, FolderForm, MoveFileForm

# Create your views here.
@login_required
def home(request):
    # Retrieve only the logged-in user's folders and files
    user = request.user
    # Get only top-level folders (folders that do not have a parent)
    folders = Folder.objects.filter(user=user, parent_folder__isnull=True)
    files = UploadedFile.objects.filter(user=user)

    # Prepare data for the template
    users_data = {
        user.username: {
            'folders': folders,
            'files': files,
            'folder_sizes': {folder.id: get_folder_size(folder) for folder in folders}
        }
    }

    context = {
        'current_user': user,
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
    # Define a custom form without help text
    class CustomUserCreationForm(UserCreationForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Remove help text for username, password1, and password2 fields
            self.fields['username'].help_text = ''
            self.fields['password1'].help_text = ''
            self.fields['password2'].help_text = ''

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created!')
            return redirect('login')
        else:
            print(form.errors)
            messages.error(request, 'Error in form submission. Please try again.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'signup.html', {'form': form})
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
            messages.error(request, 'Error creating folder. Please try again.')
    else:
        form = FolderForm()
    return render(request, 'create_folder.html', {'form': form})

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
            return redirect('view_folder', folder_id=folder.id)
        else:
            messages.error(request, 'Error renaming folder. Please try again.')
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
    messages.success(request, 'Folder moved successfully!')
    return redirect('main')

@login_required
def preview_file(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    mime_type = mimetypes.guess_type(uploaded_file.file.url)[0]
    absolute_url = request.build_absolute_uri(uploaded_file.file.url)

    # Identify file types
    is_image = mime_type and mime_type.startswith('image')
    is_video = mime_type and mime_type.startswith('video')
    is_audio = mime_type and mime_type.startswith('audio')
    is_pdf = uploaded_file.file.name.lower().endswith('.pdf')
    is_doc = uploaded_file.file.name.lower().endswith(('.doc', '.docx'))
    is_text = mime_type and mime_type.startswith('text')
    is_notebook = uploaded_file.file.name.lower().endswith('.ipynb')

    # Process PDF file to generate preview images for all pages
    preview_images_urls = []
    if is_pdf:
        # Ensure the 'media' directory exists
        media_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        if not os.path.exists(media_dir):
            os.makedirs(media_dir)
        
        # Convert all pages of the PDF to images
        poppler_path = r"C:\Program Files\poppler-24.08.0\Library\bin"  # Update this path as needed
        images = convert_from_path(uploaded_file.file.path, poppler_path=poppler_path)
        
        # Save each image with a unique name and add it to the list
        for page_num, image in enumerate(images, start=1):
            image_path = os.path.join(media_dir, f'{file_id}_page_{page_num}.jpg')
            image.save(image_path, 'JPEG')
            preview_images_urls.append(os.path.join(settings.MEDIA_URL, 'temp', f'{file_id}_page_{page_num}.jpg'))

    # Process Jupyter notebook (.ipynb) files for display
    notebook_content = ""
    if is_notebook:
        with open(uploaded_file.file.path) as f:
            nb = nbformat.read(f, as_version=4)
        notebook_content = nbformat.writes(nb)  # Convert notebook to HTML-like format

    # Syntax-highlighted content for code files (e.g., .py, .html, .css)
    formatted_text = ""
    if is_text:
        with open(uploaded_file.file.path, 'r') as f:
            content = f.read()
            lexer = {
                'html': HtmlLexer(),
                'css': CssLexer(),
                'py': PythonLexer()
            }.get(uploaded_file.file.name.split('.')[-1], TextLexer())
            formatter = HtmlFormatter(style='colorful')
            formatted_text = highlight(content, lexer, formatter)

    context = {
        'uploaded_file': uploaded_file,
        'mime_type': mime_type,
        'absolute_url': absolute_url,
        'is_image': is_image,
        'is_video': is_video,
        'is_audio': is_audio,
        'is_pdf': is_pdf,
        'is_doc': is_doc,
        'is_text': is_text,
        'is_notebook': is_notebook,
        'notebook_content': notebook_content,
        'formatted_text': formatted_text,
        'preview_images_urls': preview_images_urls,  # Pass the list of image URLs
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
            messages.error(request, 'Error moving file. Please try again.')
    else:
        form = MoveFileForm(user=request.user)

    return render(request, 'move_file.html', {'form': form, 'file': uploaded_file})

@login_required
def move_file_to_main(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    
    if request.method == 'POST':
        # Move the file back to the main page (no folder)
        uploaded_file.folder = None
        uploaded_file.save()

        # Inform the user
        messages.success(request, 'File moved to the main menu.')
        return redirect('main')
    
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

    def duplicate_folder(folder, parent=None):
        new_folder = Folder.objects.create(
            name=f"{folder.name} (Copy)",
            user=folder.user,
            parent_folder=parent
        )

        for file in folder.files.all():
            file_path = os.path.join(settings.MEDIA_ROOT, file.file.name)
            if os.path.exists(file_path):  # Check if the file exists
                UploadedFile.objects.create(
                    file=file.file,
                    folder=new_folder,
                    file_size=file.file_size,
                    uploaded_at=file.uploaded_at,
                    user=file.user
                )
            else:
                print(f"File not found: {file.file.name}")  # Log missing file info

        for subfolder in folder.subfolders.all():
            duplicate_folder(subfolder, new_folder)

    duplicate_folder(original_folder)

    messages.success(request, f"Folder '{original_folder.name}' and its contents have been copied successfully.")
    return redirect('main')

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
    # Get all files instead of filtering by the current user
    all_files = UploadedFile.objects.all()

    # Define file type categories
    file_categories = {
        'images': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'tiff'],
        'videos': ['mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv'],
        'documents': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt'],
        'audio': ['mp3', 'wav', 'aac', 'flac', 'ogg'],
        'archives': ['zip', 'rar', 'tar', 'gz', '7z'],
        # Add other categories as needed
    }

    # Categorize files
    categorized_counts = Counter()
    uncategorized_count = 0

    for file in all_files:
        extension = file.file.name.split('.')[-1].lower()
        categorized = False

        for category, extensions in file_categories.items():
            if extension in extensions:
                categorized_counts[category] += 1
                categorized = True
                break
        
        if not categorized:
            uncategorized_count += 1  # Count files with unknown extensions

    # Convert to labels and counts for the chart
    category_labels = list(categorized_counts.keys())
    category_counts = list(categorized_counts.values())

    if uncategorized_count > 0:
        category_labels.append('Other')
        category_counts.append(uncategorized_count)

    # 2. Storage Usage Over Time
    current_year = timezone.now().year
    monthly_usage = []

    for month in range(1, 13):
        month_files = UploadedFile.objects.filter(
            uploaded_at__year=current_year,
            uploaded_at__month=month
        )
        total_size = month_files.aggregate(total=Sum('file_size'))['total'] or 0
        monthly_usage.append(total_size / (1024 * 1024))  # Convert to MB

    month_labels = [calendar.month_abbr[m] for m in range(1, 13)]

    # Pass all necessary data to the template context
    context = {
        'category_labels': category_labels,
        'category_counts': category_counts,
        'month_labels': month_labels,
        'monthly_usage': monthly_usage,
    }
    
    return render(request, 'file_drive_stats.html', context)

@login_required
def profile(request):
    folder_count = Folder.objects.filter(user=request.user).count()
    file_count = UploadedFile.objects.filter(user=request.user).count()
    context = {
        'user': request.user,
        'folder_count': folder_count,
        'file_count': file_count,
    }
    return render(request, 'profile.html', context)