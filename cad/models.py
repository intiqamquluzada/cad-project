from django.db import models
from services.mixin import DateMixin, SlugMixin


class SomeDetails(DateMixin, SlugMixin):
    logo = models.ImageField(upload_to="logo/")
    right_image = models.ImageField(upload_to="right-image/")


