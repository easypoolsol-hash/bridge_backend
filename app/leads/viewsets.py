"""
Leads API ViewSets
Following Google/Fortune 500 best practices with zero-trust security
"""

from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Lead
from .models_forms import FormTemplate
from .permissions import IsAgentOwner
from .serializers import (
    FormTemplateSerializer,
    LeadCreateSerializer,
    LeadDetailSerializer,
    LeadListSerializer,
    LeadSubmitSerializer,
    PublicFormSubmissionSerializer,
)


class LeadFilter(filters.FilterSet):
    """Filtering for leads"""

    status = filters.ChoiceFilter(choices=Lead.STATUS_CHOICES)
    product = filters.NumberFilter(field_name="product__id")
    sub_category = filters.NumberFilter(field_name="product__sub_category__id")
    created_after = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Lead
        fields = ["status", "product", "sub_category", "created_after", "created_before"]


@extend_schema_view(
    list=extend_schema(
        summary="List agent's leads",
        description="Returns all leads created by the authenticated agent",
        tags=["Leads"],
    ),
    create=extend_schema(
        summary="Create a new lead",
        description="Create a lead and auto-assign to current agent",
        tags=["Leads"],
    ),
    retrieve=extend_schema(
        summary="Get lead details",
        description="Get full details of a specific lead including activities",
        tags=["Leads"],
    ),
    update=extend_schema(
        summary="Update lead",
        description="Update lead information",
        tags=["Leads"],
    ),
    partial_update=extend_schema(
        summary="Partially update lead",
        description="Update specific fields of a lead",
        tags=["Leads"],
    ),
    destroy=extend_schema(
        summary="Delete lead",
        description="Delete a draft lead (submitted leads cannot be deleted)",
        tags=["Leads"],
    ),
)
class LeadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing leads
    Agents can only see their own leads (zero-trust)
    """

    permission_classes = [IsAuthenticated, IsAgentOwner]
    filterset_class = LeadFilter
    search_fields = ["reference_number", "customer_name", "customer_phone", "customer_email"]
    ordering_fields = ["created_at", "updated_at", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Return leads for current agent only
        Admins can see all leads
        """
        user = self.request.user

        # Admins see all leads
        if user.is_staff or user.is_superuser:
            return Lead.objects.select_related(
                "product",
                "product__sub_category",
                "product__sub_category__main_category",
                "agent",
                "agent__user",
            ).prefetch_related("activities")

        # Agents see only their leads
        if hasattr(user, "agent_profile"):
            return (
                Lead.objects.filter(agent=user.agent_profile)
                .select_related(
                    "product",
                    "product__sub_category",
                    "product__sub_category__main_category",
                    "agent",
                    "agent__user",
                )
                .prefetch_related("activities")
            )

        # Users without agent profile see nothing
        return Lead.objects.none()

    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == "retrieve":
            return LeadDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return LeadCreateSerializer
        elif self.action == "submit":
            return LeadSubmitSerializer
        return LeadListSerializer

    def perform_destroy(self, instance):
        """Only allow deleting draft leads"""
        if instance.status != "draft":
            raise serializers.ValidationError("Only draft leads can be deleted")
        super().perform_destroy(instance)

    @extend_schema(
        summary="Submit a draft lead",
        description="Change lead status from draft to submitted",
        tags=["Leads"],
        request=LeadSubmitSerializer,
        responses={200: LeadDetailSerializer},
    )
    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """Submit a draft lead"""
        lead = self.get_object()

        if lead.status != "draft":
            return Response(
                {"error": "Only draft leads can be submitted"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data, context={"lead": lead, "request": request})
        serializer.is_valid(raise_exception=True)
        updated_lead = serializer.save()

        # Return updated lead
        detail_serializer = LeadDetailSerializer(updated_lead)
        return Response(detail_serializer.data)

    @extend_schema(
        summary="Get agent statistics",
        description="Get lead statistics for the current agent",
        tags=["Leads"],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "total_leads": {"type": "integer"},
                    "draft_leads": {"type": "integer"},
                    "submitted_leads": {"type": "integer"},
                    "in_progress_leads": {"type": "integer"},
                    "converted_leads": {"type": "integer"},
                    "rejected_leads": {"type": "integer"},
                },
            }
        },
    )
    @action(detail=False, methods=["get"])
    def my_stats(self, request):
        """Get statistics for current agent"""
        queryset = self.get_queryset()

        stats = {
            "total_leads": queryset.count(),
            "draft_leads": queryset.filter(status="draft").count(),
            "submitted_leads": queryset.filter(status="submitted").count(),
            "in_progress_leads": queryset.filter(status="in_progress").count(),
            "converted_leads": queryset.filter(status="converted").count(),
            "rejected_leads": queryset.filter(status="rejected").count(),
        }

        return Response(stats)


# ============================================================================
# FORM TEMPLATE VIEWSETS (Dynamic Forms)
# ============================================================================


@extend_schema_view(
    list=extend_schema(
        summary="List available form templates",
        description="Get all active form templates for creating leads",
        tags=["Forms"],
    ),
    retrieve=extend_schema(
        summary="Get form template details",
        description="Get schema and details for a specific form template",
        tags=["Forms"],
    ),
)
class FormTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for form templates
    Agents can see all active forms
    """

    permission_classes = [IsAuthenticated]
    serializer_class = FormTemplateSerializer
    queryset = FormTemplate.objects.filter(is_active=True).select_related("product")
    ordering = ["title"]


@extend_schema(
    summary="Get public form by share token",
    description="Retrieve form template for public submission (no auth required)",
    tags=["Forms - Public"],
)
@extend_schema(
    summary="Submit public form",
    description="Submit form data via public share link (no auth required)",
    tags=["Forms - Public"],
    request=PublicFormSubmissionSerializer,
    responses={201: LeadDetailSerializer},
)
class PublicFormViewSet(viewsets.ViewSet):
    """
    Public form viewset (no authentication required)
    Handles both form retrieval and submission via share token
    """

    permission_classes = []  # No authentication required

    def retrieve(self, request, share_token=None):
        """
        GET /api/public/forms/{share_token}/
        Get form template for filling
        """
        try:
            form_template = FormTemplate.objects.get(
                share_token=share_token, is_shareable=True, is_active=True
            )
        except FormTemplate.DoesNotExist:
            return Response(
                {"error": "Form not found or not accessible"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check expiry if set
        if form_template.share_expiry:
            from django.utils import timezone

            if timezone.now() > form_template.share_expiry:
                return Response(
                    {"error": "This form link has expired"},
                    status=status.HTTP_410_GONE,
                )

        serializer = FormTemplateSerializer(form_template)
        return Response(serializer.data)

    def create(self, request, share_token=None):
        """
        POST /api/public/forms/{share_token}/submit/
        Submit form data publicly
        """
        try:
            form_template = FormTemplate.objects.get(
                share_token=share_token, is_shareable=True, is_active=True
            )
        except FormTemplate.DoesNotExist:
            return Response(
                {"error": "Form not found or not accessible"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check expiry
        if form_template.share_expiry:
            from django.utils import timezone

            if timezone.now() > form_template.share_expiry:
                return Response(
                    {"error": "This form link has expired"},
                    status=status.HTTP_410_GONE,
                )

        # Validate and create submission
        serializer = PublicFormSubmissionSerializer(
            data=request.data, context={"form_template": form_template}
        )
        serializer.is_valid(raise_exception=True)
        lead = serializer.save()

        # Return created lead details
        detail_serializer = LeadDetailSerializer(lead)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
