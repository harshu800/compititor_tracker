"""
Regression coverage for app/models/column_types.py::GUID.

This exists because of a real bug: SQLAlchemy's generic Uuid(as_uuid=True)
type requires an already-parsed uuid.UUID on non-Postgres dialects, but
plain strings flow through the app legitimately at several boundaries
(the X-Organization-Id HTTP header, Celery task arguments). Postgres's
driver silently accepts strings; SQLite (used for the zero-install trial
mode) does not, and raised AttributeError: 'str' object has no attribute
'hex' the first time a real request path was exercised end-to-end rather
than via direct ORM object manipulation. GUID normalizes both forms on
every dialect. These tests exercise it directly against SQLite so a
future change to this type can't reintroduce the bug silently.
"""
import os
import uuid

os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "sqlite:///./test_column_types.db")

from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.models.column_types import GUID

Base = declarative_base()


class Widget(Base):
    __tablename__ = "guid_test_widgets"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    label = Column(String)


engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)


def test_filters_correctly_by_plain_string_id():
    """This is the exact bug: a string id (as arrives from an HTTP header
    or a Celery task argument) must work in a query filter, not just at
    insert time."""
    session = Session()
    real_id = uuid.uuid4()
    session.add(Widget(id=real_id, label="from-uuid-object"))
    session.commit()

    found = session.query(Widget).filter(Widget.id == str(real_id)).first()
    assert found is not None
    assert found.label == "from-uuid-object"
    session.close()


def test_filters_correctly_by_uuid_object_id():
    session = Session()
    real_id = uuid.uuid4()
    session.add(Widget(id=real_id, label="direct-uuid"))
    session.commit()

    found = session.query(Widget).filter(Widget.id == real_id).first()
    assert found is not None
    session.close()


def test_round_trip_preserves_value_and_returns_uuid_instance():
    session = Session()
    real_id = uuid.uuid4()
    session.add(Widget(id=real_id, label="round-trip"))
    session.commit()
    session.expunge_all()

    fetched = session.query(Widget).filter(Widget.id == str(real_id)).first()
    assert isinstance(fetched.id, uuid.UUID)
    assert fetched.id == real_id
    session.close()


def test_insert_with_plain_string_id_also_works():
    """Covers writes, not just reads — e.g. a foreign key value assembled
    from a string before the row is flushed."""
    session = Session()
    string_id = str(uuid.uuid4())
    session.add(Widget(id=string_id, label="inserted-as-string"))
    session.commit()

    found = session.query(Widget).filter(Widget.id == string_id).first()
    assert found is not None
    assert found.label == "inserted-as-string"
    session.close()


def test_none_is_preserved():
    from app.models.column_types import GUID
    guid_type = GUID()

    class FakeDialect:
        name = "sqlite"

    assert guid_type.process_bind_param(None, FakeDialect()) is None
    assert guid_type.process_result_value(None, FakeDialect()) is None
