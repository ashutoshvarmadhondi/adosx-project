from django.db import models


class Organization(models.Model):
    org_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return f"{self.org_id} - {self.name}"


class Location(models.Model):
    location_id = models.CharField(max_length=20, unique=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="locations",
    )
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return f"{self.location_id} - {self.name}"
