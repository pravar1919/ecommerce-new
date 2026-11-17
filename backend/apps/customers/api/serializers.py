import re

from rest_framework import serializers

from ..models import GSTIN_RE, INDIAN_MOBILE_RE, PINCODE_RE, Address, CustomerProfile, MeasurementProfile


def normalise_indian_mobile(value: str) -> str:
    digits = re.sub(r"[^\d+]", "", value)
    if re.fullmatch(r"[6-9]\d{9}", digits):
        digits = "+91" + digits
    elif re.fullmatch(r"91[6-9]\d{9}", digits):
        digits = "+" + digits
    if not re.fullmatch(INDIAN_MOBILE_RE, digits):
        raise serializers.ValidationError("Enter a valid 10-digit Indian mobile number.")
    return digits


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False, min_length=10)
    first_name = serializers.CharField(max_length=80)
    last_name = serializers.CharField(max_length=80, required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    marketing_opt_in = serializers.BooleanField(default=False)

    def validate_phone(self, value):
        return normalise_indian_mobile(value) if value else None


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", max_length=80)
    last_name = serializers.CharField(source="user.last_name", max_length=80, allow_blank=True)

    class Meta:
        model = CustomerProfile
        fields = [
            "email",
            "first_name",
            "last_name",
            "marketing_email_opt_in",
            "marketing_sms_opt_in",
            "preferred_size",
        ]


class AddressSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source="get_state_code_display", read_only=True)

    class Meta:
        model = Address
        fields = [
            "id",
            "full_name",
            "phone",
            "line1",
            "line2",
            "landmark",
            "city",
            "state_code",
            "state_name",
            "pincode",
            "country",
            "gstin",
            "is_default_shipping",
            "is_default_billing",
        ]
        read_only_fields = ["id", "country"]

    def validate_phone(self, value):
        return normalise_indian_mobile(value)

    def validate_pincode(self, value):
        value = value.strip()
        if not re.fullmatch(PINCODE_RE, value):
            raise serializers.ValidationError("Enter a valid 6-digit pincode.")
        return value

    def validate_gstin(self, value):
        value = value.strip().upper()
        if value and not re.fullmatch(GSTIN_RE, value):
            raise serializers.ValidationError("Enter a valid 15-character GSTIN.")
        return value


class MeasurementProfileSerializer(serializers.ModelSerializer):
    body_measurements = serializers.DictField(
        child=serializers.DecimalField(max_digits=5, decimal_places=1, coerce_to_string=True),
        help_text="Keys from /catalog/measurement-guide/, values in centimetres",
    )

    class Meta:
        model = MeasurementProfile
        fields = [
            "id",
            "label",
            "body_measurements",
            "height_cm",
            "weight_kg",
            "posture_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
