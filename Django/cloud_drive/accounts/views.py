from django.shortcuts import render,redirect
from django.template import loader
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def main(request):
    if request.user.is_authenticated:
        print(f'Logged in user: {request.user.username}')
    else:
        print('No user is logged in')
    return render(request,'main.html')

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

def logout(request):
    return HttpResponse('logout')