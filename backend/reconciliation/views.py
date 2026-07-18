from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from reconciliation.models import ReconciliationException, ReasonCode
from reconciliation.serializers import ReconciliationExceptionSerializer
from tenants.db_context import tenant_database_context
from reconciliation.qa_service import build_grounded_answer
from reconciliation.serializers import (
    ExceptionQuestionSerializer,
    ReconciliationExceptionSerializer,
)


class ReconciliationExceptionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            organization = request.user.profile.organization
        except ObjectDoesNotExist:
            return Response(
                {
                    "detail": (
                        "The authenticated user is not associated "
                        "with an organization."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        reason_code = request.query_params.get("reason_code")
        record_id = request.query_params.get("record_id")
        location_id = request.query_params.get("location_id")

        valid_reason_codes = {
            choice.value for choice in ReasonCode
        }

        if reason_code and reason_code not in valid_reason_codes:
            return Response(
                {
                    "detail": "Invalid reason_code.",
                    "valid_reason_codes": sorted(valid_reason_codes),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with tenant_database_context(organization):
            queryset = (
                ReconciliationException.objects
                .select_related("organization", "location")
                .order_by("-created_at", "record_id")
            )

            if reason_code:
                queryset = queryset.filter(
                    reason_code=reason_code
                )

            if record_id:
                queryset = queryset.filter(
                    record_id__iexact=record_id.strip()
                )

            if location_id:
                queryset = queryset.filter(
                    location__location_id__iexact=location_id.strip()
                )

            serialized_data = ReconciliationExceptionSerializer(
                queryset,
                many=True,
            ).data

        return Response(
            {
                "count": len(serialized_data),
                "results": serialized_data,
            }
        )


class ReconciliationExceptionQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request_serializer = ExceptionQuestionSerializer(
            data=request.data
        )
        request_serializer.is_valid(raise_exception=True)

        try:
            organization = request.user.profile.organization
        except ObjectDoesNotExist:
            return Response(
                {
                    "detail": (
                        "The authenticated user is not associated "
                        "with an organization."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        question = request_serializer.validated_data["question"]

        with tenant_database_context(organization):
            queryset = (
                ReconciliationException.objects
                .select_related("organization", "location")
            )

            grounded_answer = build_grounded_answer(
                question=question,
                queryset=queryset,
            )

        return Response(
            {
                "answer": grounded_answer.answer,
                "citations": grounded_answer.citations,
                "supported": grounded_answer.supported,
            }
        )
