from rest_framework import serializers

from reconciliation.models import ReconciliationException


class ReconciliationExceptionSerializer(serializers.ModelSerializer):
    organization_id = serializers.CharField(
        source="organization.org_id",
        read_only=True,
    )
    location_id = serializers.CharField(
        source="location.location_id",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = ReconciliationException
        fields = [
            "id",
            "organization_id",
            "location_id",
            "record_id",
            "reason_code",
            "reason",
            "system_a_record_id",
            "system_b_entry_ids",
            "evidence",
            "created_at",
        ]
