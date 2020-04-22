from django.db import models


class Skillet(models.Model):
    skillet_id = models.CharField(max_length=200, unique=True)


class Collection(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    categories = models.CharField(max_length=64, default="[]")
    skillets = models.ManyToManyField(Skillet)



