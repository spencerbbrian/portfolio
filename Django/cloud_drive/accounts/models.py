from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Folder(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    parent_folder = models.ForeignKey('self', null=True, blank=True, related_name='subfolders', on_delete=models.CASCADE)
    size = models.PositiveIntegerField(default=0)

    def update_size(self):
    # Calculate the total size from files and subfolders
        files_size = sum(file.file_size for file in self.files.all())  # Change to self.files.all()
        subfolders_size = sum(subfolder.size for subfolder in self.subfolders.all())
        
        # Debug output
        print(f"Updating size for '{self.name}': files_size={files_size}, subfolders_size={subfolders_size}")
        
        # Update the size and save
        self.size = files_size + subfolders_size
        self.save()


    def get_all_subfolder_ids(self):
        subfolder_ids = []

        def get_subfolder_ids(folder):
            for subfolder in folder.subfolders.all():
                subfolder_ids.append(subfolder.id)
                get_subfolder_ids(subfolder)

        get_subfolder_ids(self)
        return subfolder_ids

    def __str__(self):
        return self.name


class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True, related_name='files')  # Add related_name='files'
    file_size = models.PositiveIntegerField(default=0)  # Default size to 0

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size  # Set the size of the uploaded file
        super().save(*args, **kwargs)

    def __str__(self):
        return self.file.name
