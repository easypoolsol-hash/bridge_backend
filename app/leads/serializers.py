"""
Leads API Serializers
Following Google/Fortune 500 best practices
"""

from rest_framework import serializers
from django.core.files.base import ContentFile

from products.models import Product, SubCategory
from products.serializers import ProductListSerializer, SubCategorySerializer

from .models import Lead, LeadActivity, Client
from .models_forms import FormTemplate
from .pdf_generator import generate_lead_pdf, get_pdf_filename
from django.db.models import Count


# ============================================================================
# CLIENT SERIALIZERS
# ============================================================================


class ClientListSerializer(serializers.ModelSerializer):
    """
    Client list serializer with lead count
    Used for client list view
    """

    lead_count = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            "id",
            "name",
            "phone",
            "email",
            "lead_count",
            "created_at",
        ]
        read_only_fields = fields

    def get_lead_count(self, obj):
        """Get count of leads for this client"""
        return obj.leads.count()


class ClientDetailSerializer(serializers.ModelSerializer):
    """
    Client detail serializer with all leads
    Used for client detail view
    """

    leads = serializers.SerializerMethodField()
    lead_count = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            "id",
            "name",
            "phone",
            "email",
            "lead_count",
            "leads",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_lead_count(self, obj):
        """Get count of leads for this client"""
        return obj.leads.count()

    def get_leads(self, obj):
        """Get all leads for this client"""
        from .models import Lead
        leads = obj.leads.select_related(
            "product",
            "product__sub_category",
            "agent",
            "agent__user",
        ).order_by("-created_at")
        return LeadListSerializer(leads, many=True).data


# ============================================================================
# LEAD SERIALIZERS
# ============================================================================


class LeadListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for lead lists
    Used in agent dashboard
    """

    product_name = serializers.CharField(source="product.name", read_only=True)
    sub_category_name = serializers.CharField(source="product.sub_category.name", read_only=True)
    agent_code = serializers.CharField(source="agent.agent_code", read_only=True)
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = [
            "id",
            "reference_number",
            "product",
            "product_name",
            "sub_category_name",
            "agent_code",
            "client",
            "customer_name",
            "customer_email",
            "customer_phone",
            "status",
            "source",
            "pdf_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "reference_number",
            "agent_code",
            "client",
            "pdf_url",
            "created_at",
            "updated_at",
        ]

    def get_pdf_url(self, obj):
        """Get PDF download URL - returns absolute URL for mobile app"""
        if obj.pdf_file:
            # Get the relative URL from storage backend
            relative_url = obj.pdf_file.url

            # If URL is already absolute (starts with http), return as-is
            if relative_url.startswith('http'):
                return relative_url

            # Otherwise, build absolute URL from request context
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(relative_url)

            # Fallback: return relative URL (shouldn't happen in API)
            return relative_url
        return None


class LeadActivitySerializer(serializers.ModelSerializer):
    """
    Lead activity timeline
    """

    user_name = serializers.SerializerMethodField()

    class Meta:
        model = LeadActivity
        fields = [
            "id",
            "activity_type",
            "description",
            "user_name",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields

    def get_user_name(self, obj):
        """Get username or 'System' if no user"""
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return "System"


class LeadDetailSerializer(serializers.ModelSerializer):
    """
    Full lead details with activities
    """

    product = ProductListSerializer(read_only=True)
    sub_category = SubCategorySerializer(source="product.sub_category", read_only=True)
    agent_code = serializers.CharField(source="agent.agent_code", read_only=True)
    agent_name = serializers.SerializerMethodField()
    activities = LeadActivitySerializer(many=True, read_only=True)
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = [
            "id",
            "reference_number",
            "product",
            "sub_category",
            "agent_code",
            "agent_name",
            "client",
            "customer_name",
            "customer_email",
            "customer_phone",
            "form_data",
            "source",
            "referral_code",
            "status",
            "assigned_to",
            "pdf_url",
            "activities",
            "created_at",
            "updated_at",
            "converted_at",
        ]
        read_only_fields = [
            "id",
            "reference_number",
            "agent_code",
            "agent_name",
            "client",
            "pdf_url",
            "activities",
            "created_at",
            "updated_at",
        ]

    def get_agent_name(self, obj):
        """Get agent's full name"""
        return obj.agent.user.get_full_name() or obj.agent.user.username

    def get_pdf_url(self, obj):
        """Get PDF download URL - returns absolute URL for mobile app"""
        if obj.pdf_file:
            # Get the relative URL from storage backend
            relative_url = obj.pdf_file.url

            # If URL is already absolute (starts with http), return as-is
            if relative_url.startswith('http'):
                return relative_url

            # Otherwise, build absolute URL from request context
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(relative_url)

            # Fallback: return relative URL (shouldn't happen in API)
            return relative_url
        return None


class LeadCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating leads
    Auto-assigns agent from Firebase authentication
    """

    product_id = serializers.IntegerField(write_only=True)
    sub_category_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Lead
        fields = [
            "id",
            "product_id",
            "sub_category_id",
            "customer_name",
            "customer_email",
            "customer_phone",
            "form_data",
            "source",
            "referral_code",
            "status",
        ]
        read_only_fields = ["id"]

    def validate_product_id(self, value):
        """Validate product exists and is active"""
        try:
            product = Product.objects.get(id=value, active=True)
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Invalid product ID or product is not active")

    def validate_sub_category_id(self, value):
        """Validate sub-category exists and is active"""
        if value:
            try:
                SubCategory.objects.get(id=value, active=True)
                return value
            except SubCategory.DoesNotExist:
                raise serializers.ValidationError(
                    "Invalid sub-category ID or sub-category is not active"
                )
        return value

    def create(self, validated_data):
        """
        Create lead and auto-assign to current agent
        Uses Google-style client resolution: find or create client
        """
        product_id = validated_data.pop("product_id")
        validated_data.pop("sub_category_id", None)  # Remove if present

        # Get product
        product = Product.objects.get(id=product_id)

        # Get agent from authenticated user
        user = self.context["request"].user
        if not hasattr(user, "agent_profile"):
            raise serializers.ValidationError(
                "User must have an agent profile to create leads"
            )

        # ============================================
        # CLIENT RESOLUTION (Google-style)
        # ============================================
        customer_phone = validated_data.get("customer_phone", "").strip()
        customer_email = validated_data.get("customer_email", "").strip()
        customer_name = validated_data.get("customer_name", "").strip()

        client = None

        # Try to find existing client by phone (primary identifier)
        if customer_phone:
            client = Client.objects.filter(phone=customer_phone).first()

        # Fallback: try to find by email if phone lookup failed
        if not client and customer_email:
            client = Client.objects.filter(email=customer_email).first()

        # If no existing client found, create new one
        if not client:
            client = Client.objects.create(
                phone=customer_phone or "",
                email=customer_email or "",
                name=customer_name,
            )

        # Create lead with resolved client
        lead = Lead.objects.create(
            product=product,
            agent=user.agent_profile,
            client=client,
            **validated_data
        )

        # Create activity
        LeadActivity.objects.create(
            lead=lead,
            user=user,
            activity_type="created",
            description=f"Lead created by agent {user.agent_profile.agent_code}",
        )

        # Generate and save PDF (auto-generation on submission)
        try:
            pdf_bytes = generate_lead_pdf(lead)
            pdf_filename = get_pdf_filename(lead)
            lead.pdf_file.save(pdf_filename, ContentFile(pdf_bytes), save=True)
        except Exception as e:
            # Log error but don't fail lead creation
            print(f"[PDF] Failed to generate PDF for lead {lead.reference_number}: {e}")

        return lead

    def update(self, instance, validated_data):
        """Update lead and log activity"""
        validated_data.pop("product_id", None)  # Can't change product after creation
        validated_data.pop("sub_category_id", None)

        # Track status changes
        old_status = instance.status
        new_status = validated_data.get("status", old_status)

        # Update lead
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Log status change if changed
        if old_status != new_status:
            LeadActivity.objects.create(
                lead=instance,
                user=self.context["request"].user,
                activity_type="status_change",
                description=f"Status changed from {old_status} to {new_status}",
                metadata={"old_status": old_status, "new_status": new_status},
            )

        return instance


class LeadSubmitSerializer(serializers.Serializer):
    """
    Serializer for submitting a draft lead
    """

    notes = serializers.CharField(required=False, allow_blank=True)

    def save(self, **kwargs):
        """Submit the lead"""
        lead = self.context["lead"]
        user = self.context["request"].user

        # Update status
        lead.status = "submitted"
        lead.save()

        # Create activity
        notes = self.validated_data.get("notes", "")
        description = "Lead submitted"
        if notes:
            description += f": {notes}"

        LeadActivity.objects.create(
            lead=lead,
            user=user,
            activity_type="status_change",
            description=description,
            metadata={"old_status": "draft", "new_status": "submitted"},
        )

        return lead


# ============================================================================
# FORM TEMPLATE SERIALIZERS (Dynamic Forms)
# ============================================================================


class FormTemplateSerializer(serializers.ModelSerializer):
    """
    Form template for dynamic forms
    Used by agents to see available forms and by public for shared forms
    """

    product_name = serializers.CharField(source="product.name", read_only=True, allow_null=True)
    share_url = serializers.SerializerMethodField()

    class Meta:
        model = FormTemplate
        fields = [
            "id",
            "title",
            "description",
            "product",
            "product_name",
            "schema",
            "is_shareable",
            "share_url",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "share_url", "created_at"]

    def get_share_url(self, obj):
        """Get share URL if form is shareable"""
        return obj.share_url if obj.is_shareable else None


class PublicFormSubmissionSerializer(serializers.Serializer):
    """
    Public form submission (for share links)
    Minimal validation - accepts form_data as-is from frontend
    """

    form_data = serializers.JSONField()
    customer_name = serializers.CharField(max_length=200)
    customer_email = serializers.EmailField(required=False, allow_blank=True)
    customer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    referral_code = serializers.CharField(max_length=50, required=False, allow_blank=True)

    def validate_form_data(self, value):
        """Basic validation - ensure it's a dict"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("form_data must be a JSON object")
        return value

    def create(self, validated_data):
        """
        Create lead from public submission
        No agent assigned (null)
        Uses Google-style client resolution
        """
        form_template = self.context["form_template"]

        # ============================================
        # CLIENT RESOLUTION (Google-style)
        # ============================================
        customer_phone = validated_data.get("customer_phone", "").strip()
        customer_email = validated_data.get("customer_email", "").strip()
        customer_name = validated_data.get("customer_name", "").strip()

        client = None

        # Try to find existing client by phone (primary identifier)
        if customer_phone:
            client = Client.objects.filter(phone=customer_phone).first()

        # Fallback: try to find by email if phone lookup failed
        if not client and customer_email:
            client = Client.objects.filter(email=customer_email).first()

        # If no existing client found, create new one
        if not client:
            client = Client.objects.create(
                phone=customer_phone or "",
                email=customer_email or "",
                name=customer_name,
            )

        # Create lead without agent but with resolved client
        lead = Lead.objects.create(
            product=form_template.product,
            agent=None,  # No agent for public submissions
            form_template=form_template,
            client=client,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            form_data=validated_data["form_data"],
            source="public_share",
            referral_code=validated_data.get("referral_code", ""),
            status="submitted",
        )

        # Create activity
        LeadActivity.objects.create(
            lead=lead,
            user=None,  # No user for public submission
            activity_type="created",
            description=f"Lead created via public share link: {form_template.title}",
        )

        # Generate and save PDF (auto-generation on submission)
        try:
            pdf_bytes = generate_lead_pdf(lead)
            pdf_filename = get_pdf_filename(lead)
            lead.pdf_file.save(pdf_filename, ContentFile(pdf_bytes), save=True)
        except Exception as e:
            # Log error but don't fail lead creation
            print(f"[PDF] Failed to generate PDF for lead {lead.reference_number}: {e}")

        return lead
