from django.db import models
from backend.models import Exam, Identification, OrganUnit

class Pool(models.Model):
    name = models.CharField(max_length=250)
    identification = models.ForeignKey(Identification, null=True, blank=True, on_delete=models.CASCADE)
    organ_unit = models.ManyToManyField(to=OrganUnit, through="PoolOrganUnit")
    exams = models.ManyToManyField(to=Exam, through="PoolExam")

class PoolOrganUnit(models.Model):
    pool = models.ForeignKey(Pool, null=True, blank=True, on_delete=models.CASCADE)
    organ_unit = models.ForeignKey(OrganUnit, null=True, blank=True, on_delete=models.SET_NULL)

class PoolExam(models.Model):
    pool = models.ForeignKey(Pool, null=True, blank=True, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, null=True, blank=True, on_delete=models.SET_NULL)