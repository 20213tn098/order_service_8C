from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import AccessToken

Usuario = get_user_model()


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model  = Usuario
        fields = [
            'id', 'nombre', 'apellido', 'correo', 'password',
            'calle', 'numero_exterior', 'numero_interior',
            'colonia', 'ciudad', 'estado', 'codigo_postal', 'pais',
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        usuario  = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()
        return usuario


class TokenObtainAccessSerializer(TokenObtainSerializer):
    """Credenciales con el campo de usuario del modelo (`correo`); solo emite access JWT."""

    token_class = AccessToken

    def validate(self, attrs):
        data = super().validate(attrs)
        access = self.get_token(self.user)
        data['access'] = str(access)
        data['usuario_id'] = self.user.pk
        if jwt_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)
        return data


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    usuario_id = serializers.IntegerField()


class ErrorDetailSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.JSONField(required=False)


class ErrorResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=False)
    error = ErrorDetailSerializer()
    timestamp = serializers.DateTimeField()


class RegistroSuccessResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = RegistroSerializer()
    timestamp = serializers.DateTimeField()


class LoginSuccessResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = LoginResponseSerializer()
    timestamp = serializers.DateTimeField()


class PerfilSerializer(serializers.ModelSerializer):
    direccion_envio = serializers.SerializerMethodField()

    class Meta:
        model  = Usuario
        fields = ['id', 'nombre', 'apellido', 'correo', 'direccion_envio']

    @extend_schema_field(
        {
            'type':       'object',
            'properties': {
                'calle':           {'type': 'string'},
                'numero_exterior': {'type': 'string'},
                'numero_interior': {'type': 'string'},
                'colonia':         {'type': 'string'},
                'ciudad':          {'type': 'string'},
                'estado':          {'type': 'string'},
                'codigo_postal':   {'type': 'string'},
                'pais':            {'type': 'string'},
            },
        }
    )
    def get_direccion_envio(self, obj):
        return {
            'calle':           obj.calle,
            'numero_exterior': obj.numero_exterior,
            'numero_interior': obj.numero_interior,
            'colonia':         obj.colonia,
            'ciudad':          obj.ciudad,
            'estado':          obj.estado,
            'codigo_postal':   obj.codigo_postal,
            'pais':            obj.pais,
        }


class PerfilSuccessResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = PerfilSerializer()
    timestamp = serializers.DateTimeField()