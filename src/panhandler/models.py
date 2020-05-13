from django.db import models


class RepositoryDetails(models.Model):
    name = models.CharField(max_length=200)
    url = models.CharField(max_length=512)
    deploy_key_path = models.CharField(max_length=128, default='', null='')
    details_json = models.TextField(max_length=2048)


class Skillet(models.Model):
    name = models.CharField(max_length=200, unique=True)
    skillet_json = models.TextField(max_length=2048, default='')
    repository = models.ForeignKey(RepositoryDetails, on_delete=models.CASCADE)


class Collection(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    categories = models.CharField(max_length=64, default="[]")
    skillets = models.ManyToManyField(Skillet)
