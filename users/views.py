from users.forms import LoginForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST or None)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            print(email, password)
            user = authenticate(request, email=email, password=password)
            print(user)
            if user:
                login(request, user)
                return redirect("home")
            else:
                messages.error(request, "Email və ya şifrə səhvdir.")
                form = LoginForm()
        else:
            form = LoginForm()
    else:
        form = LoginForm()

    context = {
        "form": form,
    }
    return render(request, "login.html", context)


def logout_view(request):
    logout(request)
    return redirect("login")