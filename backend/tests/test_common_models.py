"""BaseModel and soft-delete managers (DRF_SKILL §11-13)."""

import pytest

from tests.testapp.models import Widget

pytestmark = pytest.mark.django_db


def test_create_sets_timestamps_and_is_active():
    widget = Widget.objects.create(name="a")

    assert widget.created_at is not None
    assert widget.modified_at is not None
    assert widget.deleted_at is None
    assert widget.is_deleted is False


def test_modification_updates_modified_at():
    widget = Widget.objects.create(name="a")
    before = widget.modified_at

    widget.name = "b"
    widget.save()
    widget.refresh_from_db()

    assert widget.modified_at >= before
    assert widget.created_at <= widget.modified_at


def test_soft_delete_hides_row_from_default_manager():
    widget = Widget.objects.create(name="a")

    widget.soft_delete()

    assert widget.is_deleted is True
    assert not Widget.objects.filter(pk=widget.pk).exists()
    assert Widget.deleted_objects.filter(pk=widget.pk).exists()
    assert Widget.all_objects.filter(pk=widget.pk).exists()


def test_soft_delete_is_idempotent():
    widget = Widget.objects.create(name="a")
    widget.soft_delete()
    first = widget.deleted_at

    widget.soft_delete()

    assert widget.deleted_at == first


def test_restore_brings_row_back():
    widget = Widget.objects.create(name="a")
    widget.soft_delete()

    widget.restore()
    widget.refresh_from_db()

    assert widget.deleted_at is None
    assert Widget.objects.filter(pk=widget.pk).exists()
    assert not Widget.deleted_objects.filter(pk=widget.pk).exists()


def test_restore_on_active_row_is_a_no_op():
    widget = Widget.objects.create(name="a")

    widget.restore()

    assert widget.deleted_at is None


def test_managers_partition_rows():
    active = Widget.objects.create(name="active")
    deleted = Widget.objects.create(name="deleted")
    deleted.soft_delete()

    assert list(Widget.objects.all()) == [active]
    assert list(Widget.deleted_objects.all()) == [deleted]
    assert list(Widget.all_objects.order_by("id")) == [active, deleted]
    assert Widget._default_manager.__class__.__name__ == "ActiveManager"


def test_str_uses_name():
    assert str(Widget(name="gear")) == "gear"
