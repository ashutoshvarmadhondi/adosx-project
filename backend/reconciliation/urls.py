from django.urls import path

from reconciliation.views import ReconciliationExceptionListView


urlpatterns = [
    path(
        "exceptions/",
        ReconciliationExceptionListView.as_view(),
        name="exception-list",
    ),
]
