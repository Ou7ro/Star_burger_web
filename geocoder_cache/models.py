from django.db import models
from django.utils import timezone


class CachedLocation(models.Model):
    address = models.CharField(
        'адрес',
        max_length=255,
        unique=True,
        db_index=True
    )
    latitude = models.FloatField('широта', null=True, blank=True)
    longitude = models.FloatField('долгота', null=True, blank=True)
    created_at = models.DateTimeField('дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'кэшированная локация'
        verbose_name_plural = 'кэшированные локации'
        indexes = [
            models.Index(fields=['address']),
        ]

    def __str__(self):
        return f'{self.address} ({self.latitude}, {self.longitude})'

    def is_expired(self, expiry_days=30):
        """Проверяет, устарели ли данные"""
        return (timezone.now() - self.updated_at).days > expiry_days
