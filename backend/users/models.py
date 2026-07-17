from django.db import models
from django.conf import settings
from django.db import models
from tenants.models import Organization


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="users",
    )

    def __str__(self) -> str:
        return f"{self.user.username} - {self.organization.org_id}"

# Create your models here.
