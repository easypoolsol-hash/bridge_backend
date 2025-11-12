"""
Leads API Serializers
Following Google/Fortune 500 best practices
"""

from rest_framework import serializers

from products.models import Product, SubCategory
from products.serializers import ProductListSerializer, SubCategorySerializer

from .models import Lead, LeadActivity


class LeadListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for lead lists
    Used in agent dashboard
    """

    product_name = serializers.CharField(source="product.name", read_only=True)
    sub_category_name = serializers.CharField(source="product.sub_category.name", read_only=True)
    agent_code = serializers.CharField(source="agent.agent_code", read_only=True)

    class Meta:
        model = Lead
        fields = [
            "id",
            "reference_number",
            "product",
            "product_name",
            "sub_category_name",
            "agent_code",
            "customer_name",
            "customer_email",
            "customer_phone",
            "status",
            "source",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "reference_number",
            "agent_code",
            "created_at",
            "updated_at",
        ]


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

    class Meta:
        model = Lead
        fields = [
            "id",
            "reference_number",
            "product",
            "sub_category",
            "agent_code",
            "agent_name",
            "customer_name",
            "customer_email",
            "customer_phone",
            "form_data",
            "source",
            "referral_code",
            "status",
            "assigned_to",
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
            "activities",
            "created_at",
            "updated_at",
        ]

    def get_agent_name(self, obj):
        """Get agent's full name"""
        return obj.agent.user.get_full_name() or obj.agent.user.username


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

        # Create lead
        lead = Lead.objects.create(
            product=product, agent=user.agent_profile, **validated_data
        )

        # Create activity
        LeadActivity.objects.create(
            lead=lead,
            user=user,
            activity_type="created",
            description=f"Lead created by agent {user.agent_profile.agent_code}",
        )

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
