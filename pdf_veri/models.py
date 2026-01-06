
from django.db import models

class PDFDocument(models.Model):
    file = models.FileField(upload_to='pdfs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
class VerificationHistory(models.Model):
    filename = models.CharField(max_length=255)
    change_type = models.CharField(max_length=50) # CHANGE or NO-CHANGE
    status = models.CharField(max_length=50)      # Success or Error
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField()

    def __str__(self):
        return f"{self.filename} - {self.status}"