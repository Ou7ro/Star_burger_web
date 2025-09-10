from django.contrib import admin
from .models import CachedLocation

@admin.register(CachedLocation)
class CachedLocationAdmin(admin.ModelAdmin):
    list_display = ['address', 'latitude', 'longitude', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['address']
    readonly_fields = ['created_at', 'updated_at']