from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import LetterPhoto, LoveLetter


@receiver(post_delete, sender=LetterPhoto)
def delete_photo_file(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)


@receiver(post_delete, sender=LoveLetter)
def delete_letter_files(sender, instance, **kwargs):
    if instance.music_file:
        instance.music_file.delete(save=False)
