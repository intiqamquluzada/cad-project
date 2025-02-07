from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.text import get_valid_filename
import uuid

from services.cad_creator import generate_dxf

# Initialize FileSystemStorage with MEDIA_ROOT
fs = FileSystemStorage(location=settings.MEDIA_ROOT)


def get_upload_path(filename):
    # Generate a unique filename to avoid conflicts
    unique_filename = f"{uuid.uuid4().hex}_{get_valid_filename(filename)}"
    return unique_filename


def index_view(request):
    message = None
    file_path = None

    if request.method == "POST" and request.FILES.get("file"):
        excel_file = request.FILES["file"]

        safe_filename = get_upload_path(excel_file.name)

        try:
            saved_filename = fs.save(safe_filename, excel_file)
            file_path = os.path.join(settings.MEDIA_ROOT, saved_filename)
            print("UPLOAD PATH", file_path)

            dxf_file_path = generate_dxf(file_path)
            print(dxf_file_path)

            with open(dxf_file_path, 'rb') as dxf_file:
                response = HttpResponse(dxf_file.read(), content_type='application/dxf')
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(dxf_file_path)}"'
                return response

        except Exception as e:
            message = f"An error occurred: {str(e)}"
            return render(request, "index.html", {"message": message, "file_path": None})

    return render(request, "index.html", {"message": message, "file_path": file_path})
