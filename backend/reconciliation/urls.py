from django.urls import path

from reconciliation.views import (
    ReconciliationExceptionListView,
    ReconciliationExceptionQuestionView,
)


urlpatterns = [
    path(
        "exceptions/",
        ReconciliationExceptionListView.as_view(),
        name="exception-list",
    ),

    path(
        "exceptions/ask/",
        ReconciliationExceptionQuestionView.as_view(),
        name="exception-question",
    ),
]
