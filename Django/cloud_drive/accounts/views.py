from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import UploadedFile
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UploadFileForm

# Create your views here.
@login_required
def main(request):
    if request.user.is_authenticated:
        print(f'Logged in user: {request.user.username}')
    else:
        print('No user is logged in')
    user_files = UploadedFile.objects.filter(user=request.user)
    
    return render(request,'main.html', {'user_files':user_files})

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
            if uploaded_file.file_size > 41943040:
                messages.error(request, 'File size exceeds 40MB. Please upload a smaller file.')
                return redirect('upload_file')
            else:
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
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    uploaded_file.file.delete()
    uploaded_file.delete()

    messages.success(request,'File deleted successfully!')
    return redirect('main')