# usuarios/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UsuarioManager(BaseUserManager):
    def create_user(self, correo, password=None, **extra_fields):
        if not correo:
            raise ValueError('El correo es obligatorio')
        correo = self.normalize_email(correo)
        user   = self.model(correo=correo, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, correo, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(correo, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    # Identidad
    correo   = models.EmailField(unique=True)
    nombre   = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)

    # Dirección de envío
    calle           = models.CharField(max_length=200)
    numero_exterior = models.CharField(max_length=20)
    numero_interior = models.CharField(max_length=20, blank=True, default='')
    colonia         = models.CharField(max_length=100)
    ciudad          = models.CharField(max_length=100)
    estado          = models.CharField(max_length=100)
    codigo_postal   = models.CharField(max_length=10)
    pais            = models.CharField(max_length=50, default='MX')

    # Django internals
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD  = 'correo'
    REQUIRED_FIELDS = ['nombre', 'apellido']

    objects = UsuarioManager()

    class Meta:
        db_table = 'usuarios'

    def __str__(self):
        return f"{self.nombre} {self.apellido} <{self.correo}>"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"