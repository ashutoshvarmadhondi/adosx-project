from contextlib import contextmanager
from typing import Iterator

from django.db import connection, transaction

from tenants.models import Organization


@contextmanager
def tenant_database_context(
    organization: Organization,
) -> Iterator[None]:
    """
    Set the PostgreSQL tenant context for the current transaction.

    RLS policies use app.current_org_id to decide which rows are visible
    and which rows may be inserted or updated.
    """
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('app.current_org_id', %s, true)",
                [str(organization.pk)],
            )

        yield
