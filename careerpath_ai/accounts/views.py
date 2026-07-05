from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import NewRegisterForm

def register_view(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')
        
    if request.method == 'POST':
        form = NewRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.full_name = form.cleaned_data['full_name']
            user.save()
            
            messages.success(request, "Account created successfully! Welcome aboard. ✨")
            auth_login(request, user)
            return redirect('/dashboard/')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = NewRegisterForm()
        
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('/dashboard/')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
        
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    return redirect('landing')