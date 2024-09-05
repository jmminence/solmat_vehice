from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    name = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return self.name


LANGUAGE_OPTION = ((1, "ES"), (2, "EN"))


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario")
    role = models.CharField(max_length=250, null=True, blank=True)
    rut = models.CharField(max_length=250, null=True, blank=True)
    phone = models.CharField(
        max_length=250, null=True, blank=True, verbose_name="Teléfono"
    )
    state = models.IntegerField(default=1, null=True, blank=True)
    signing = models.CharField(
        max_length=120, blank=True, null=True, verbose_name="Firma"
    )
    signature = models.FileField(
        upload_to="signatures", blank=True, null=True, verbose_name="Firma Digital"
    )
    confirmation_code = models.CharField(max_length=250, null=True, blank=True)
    profile = models.ForeignKey(
        Profile, null=True, on_delete=models.SET_NULL, verbose_name="Rol"
    )
    is_pathologist = models.BooleanField(default=False, verbose_name="¿Es patólogo?")
    is_reviewer = models.BooleanField(default=False, verbose_name="¿Es revisor?")
    language = models.IntegerField(
        default=1, choices=LANGUAGE_OPTION, verbose_name="Lenguage"
    )

    def __str__(self):
        return self.profile.name

    def save(self, *args, **kwargs):
        if self.profile_id == 1:
            self.user.is_staff = True
            self.user.is_superuser = True
            self.user.save()

        super(UserProfile, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"


class Area(models.Model):
    name = models.CharField(max_length=255)

    users = models.ManyToManyField(User, related_name="areas", through="UserArea")

    is_deleted = models.BooleanField(verbose_name="desactivado", default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class UserArea(models.Model):
    ROLES = [(0, "jefe"), (1, "miembro")]

    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.SmallIntegerField(verbose_name="rol", choices=ROLES, default=ROLES[1])

    def __str__(self):
        return f"{self.user} es {self.get_role_display()} de {self.area}"
