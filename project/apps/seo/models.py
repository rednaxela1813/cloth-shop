from django.db import models
import uuid


'''
Самый простой и надежный вариант — отдельная модель SeoMeta в apps/seo и OneToOneField к ней в Product и Category
'''

class SeoMeta(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    keywords = models.CharField(max_length=512, blank=True, null=True)
    og_image = models.ImageField(upload_to="seo/og_images/", blank=True, null=True) # Open Graph image      
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title or str(self.public_id)