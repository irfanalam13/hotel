from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.common.permissions import IsPropertyStaff, HasPropertyObjectAccess
from .models import Property, Amenity, RoomType, Room
from .serializers import PropertySerializer, AmenitySerializer, RoomTypeSerializer, RoomSerializer

def get_property_from_header(request):
    prop_id = request.headers.get("X-PROPERTY-ID")
    return Property.objects.get(id=prop_id)

class PropertyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]

class AmenityViewSet(viewsets.ModelViewSet):
    serializer_class = AmenitySerializer
    permission_classes = [IsAuthenticated, IsPropertyStaff, HasPropertyObjectAccess]

    def get_queryset(self):
        prop = get_property_from_header(self.request)
        return Amenity.objects.filter(property=prop)

    def perform_create(self, serializer):
        prop = get_property_from_header(self.request)
        serializer.save(property=prop)

class RoomTypeViewSet(viewsets.ModelViewSet):
    serializer_class = RoomTypeSerializer
    permission_classes = [IsAuthenticated, IsPropertyStaff, HasPropertyObjectAccess]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "base_rate"]

    def get_queryset(self):
        prop = get_property_from_header(self.request)
        return RoomType.objects.filter(property=prop).prefetch_related("amenities")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["property"] = get_property_from_header(self.request)
        return ctx

    def perform_create(self, serializer):
        prop = get_property_from_header(self.request)
        serializer.save(property=prop)

class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated, IsPropertyStaff, HasPropertyObjectAccess]
    search_fields = ["number", "floor"]
    ordering_fields = ["number", "housekeeping_status"]

    def get_queryset(self):
        prop = get_property_from_header(self.request)
        return Room.objects.filter(property=prop).select_related("room_type")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["property"] = get_property_from_header(self.request)
        return ctx

    def perform_create(self, serializer):
        prop = get_property_from_header(self.request)
        serializer.save(property=prop)
