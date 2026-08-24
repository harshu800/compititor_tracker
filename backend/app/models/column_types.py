"""
Cross-dialect UUID column type.

Postgres's native UUID type (and its drivers) happily accept a plain
Python string as a bind parameter and coerce it — so `filter(Model.id ==
"abc-123...")` works fine in production. SQLAlchemy's generic `Uuid`
type does NOT do this on non-Postgres dialects (e.g. SQLite, used for the
zero-install trial mode) — it requires an already-parsed `uuid.UUID`
instance, and raises `AttributeError: 'str' object has no attribute
'hex'` otherwise.

Since organization/user/resource ids flow through the app as plain
strings in several legitimate places (HTTP headers like X-Organization-Id,
Celery task arguments, which must be JSON-serializable), requiring every
call site to remember to convert to uuid.UUID before every query is a
sharp edge that's easy to get wrong. This type normalizes both forms on
the way in, on every dialect, which is exactly what Postgres already does
for us — GUID just makes that leniency portable.
"""
import uuid

from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(str(value))
        if dialect.name == "postgresql":
            return str(value)
        return value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)
        return value
