from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from apps.common.permissions import IsPropertyStaff, HasPropertyObjectAccess
from apps.properties.models import Property
from .models import Guest, GuestDocument
from .serializers import GuestSerializer, GuestDocumentSerializer

def get_property_from_header(request):
    prop_id = request.headers.get("X-PROPERTY-ID")
    return Property.objects.get(id=prop_id)

class GuestViewSet(viewsets.ModelViewSet):
    serializer_class = GuestSerializer
    permission_classes = [IsAuthenticated, IsPropertyStaff, HasPropertyObjectAccess]
    search_fields = ["first_name", "last_name", "phone", "email"]
    ordering_fields = ["created_at", "first_name"]

    def get_queryset(self):
        prop = get_property_from_header(self.request)
        return Guest.objects.filter(property=prop).prefetch_related("documents")

    def perform_create(self, serializer):
        prop = get_property_from_header(self.request)
        serializer.save(property=prop)

class GuestDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = GuestDocumentSerializer
    permission_classes = [IsAuthenticated, IsPropertyStaff, HasPropertyObjectAccess]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        prop = get_property_from_header(self.request)
        return GuestDocument.objects.filter(property=prop).select_related("guest")

    def perform_create(self, serializer):
        prop = get_property_from_header(self.request)
        guest = serializer.validated_data["guest"]
        if guest.property_id != prop.id:
            raise ValueError("Guest must belong to same property.")
        serializer.save(property=prop)
