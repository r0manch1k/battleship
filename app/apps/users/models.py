import uuid
from io import BytesIO

from django.contrib.auth.models import AbstractUser
from django.core.files import File
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image


def get_avatar_path(instance, filename):
    return f"avatars/{instance.id}/{filename}"


class User(AbstractUser):
    avatar = models.ImageField(upload_to=get_avatar_path, null=True)

    __original_avatar = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__original_avatar = self.avatar

    def save(self, *args, **kwargs):
        if self.avatar != self.__original_avatar:
            self._process_avatar((300, 300))

        super().save(*args, **kwargs)

    def _process_avatar(self, size: tuple):
        self.avatar.open()

        im = Image.open(self.avatar)

        image = im.convert("RGB")

        if image.width > image.height:
            image = image.crop(
                (
                    0.5 * (image.width - image.height),
                    0,
                    0.5 * (image.width + image.height),
                    image.height,
                )
            )
        elif image.width < image.height:
            image = image.crop(
                (
                    0,
                    0.5 * (image.height - image.width),
                    image.width,
                    0.5 * (image.height + image.width),
                )
            )

        image.thumbnail(size)

        output = BytesIO()
        image.save(output, format="webp")

        output.seek(0)
        content = ContentFile(output.read())

        file = File(content)

        filename = f"{uuid.uuid4()}.webp"

        self.avatar.save(filename, file, save=False)
