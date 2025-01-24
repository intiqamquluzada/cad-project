from django.shortcuts import render, redirect


def index_view(request):
    context = {

    }
    return render(request, "index.html", context)



