from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api.serializers import MeSerializer

from .. import services
from ..models import Address, MeasurementProfile
from .serializers import (
    AddressSerializer,
    MeasurementProfileSerializer,
    ProfileSerializer,
    RegisterSerializer,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    @extend_schema(request=RegisterSerializer, responses={201: MeSerializer}, tags=["auth"])
    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            user = services.register_customer(request, **s.validated_data)
        except DjangoValidationError as exc:
            raise ValidationError({"password": list(exc.messages)}) from exc
        return Response(MeSerializer(user).data, status=status.HTTP_201_CREATED)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=ProfileSerializer, tags=["account"])
    def get(self, request):
        return Response(ProfileSerializer(services.get_or_create_profile(request.user)).data)

    @extend_schema(request=ProfileSerializer, responses=ProfileSerializer, tags=["account"])
    def patch(self, request):
        profile = services.get_or_create_profile(request.user)
        s = ProfileSerializer(profile, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        user_data = s.validated_data.pop("user", {})
        for k, v in user_data.items():
            setattr(request.user, k, v)
        if user_data:
            request.user.save(update_fields=list(user_data))
        for k, v in s.validated_data.items():
            setattr(profile, k, v)
        profile.save()
        return Response(ProfileSerializer(profile).data)


class OwnedViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Customer-owned resources: queryset is always scoped to the requesting user (no IDOR)."""

    permission_classes = [IsAuthenticated]
    pagination_class = None
    related_name = ""

    def profile(self):
        return services.get_or_create_profile(self.request.user)

    def get_queryset(self):
        return getattr(self.profile(), self.related_name).all()


@extend_schema(tags=["account"])
class AddressViewSet(OwnedViewSet):
    serializer_class = AddressSerializer
    queryset = Address.objects.none()  # typing for OpenAPI; real queryset is owner-scoped
    related_name = "addresses"

    def perform_create(self, serializer):
        serializer.instance = services.save_address(self.profile(), **serializer.validated_data)

    def perform_update(self, serializer):
        serializer.instance = services.save_address(
            self.profile(), instance=serializer.instance, **serializer.validated_data
        )

    @extend_schema(request=None, responses=AddressSerializer)
    @action(detail=True, methods=["post"], url_path="set-default")
    def set_default(self, request, pk=None):
        address = services.set_default_address(self.get_object())
        return Response(AddressSerializer(address).data)


@extend_schema(tags=["account"])
class MeasurementProfileViewSet(OwnedViewSet):
    serializer_class = MeasurementProfileSerializer
    queryset = MeasurementProfile.objects.none()
    related_name = "measurement_profiles"

    def perform_create(self, serializer):
        serializer.instance = services.save_measurement_profile(self.profile(), **serializer.validated_data)

    def perform_update(self, serializer):
        serializer.instance = services.save_measurement_profile(
            self.profile(), instance=serializer.instance, **serializer.validated_data
        )
