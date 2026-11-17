from rest_framework import serializers

from ..models import User


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class MeSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone", "is_staff", "roles", "permissions"]
        read_only_fields = fields

    def get_roles(self, obj) -> list[str]:
        return sorted(obj.groups.values_list("name", flat=True)) if obj.is_staff else []

    def get_permissions(self, obj) -> list[str]:
        return sorted(obj.get_all_permissions()) if obj.is_staff else []


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)


class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField()
