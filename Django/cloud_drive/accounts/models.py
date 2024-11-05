from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Folder (models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    parent_folder = models.ForeignKey('self', null=True, blank=True, related_name='subfolders', on_delete=models.CASCADE)

    def get_all_subfolder_ids(self):
        # Collect all subfolder IDs recursively
        subfolder_ids = []
        
        # Recursive helper function
        def get_subfolder_ids(folder):
            for subfolder in folder.subfolders.all():
                subfolder_ids.append(subfolder.id)
                get_subfolder_ids(subfolder)  # Recursively get sub-subfolder IDs
        
        get_subfolder_ids(self)  # Start with the current folder
        return subfolder_ids

    def __str__(self):
        return self.name
    

class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    folder = models.ForeignKey('Folder', on_delete=models.CASCADE, null=True, blank=True)
    file_size = models.PositiveIntegerField()

    def __str__(self):
        return self.file.name
    