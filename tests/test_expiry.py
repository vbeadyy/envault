"""Tests for envault.expiry module."""

import time

import pytest

from envault.expiry import (
    ExpiryError,
    ExpiryRecord,
    get_expired_keys,
    get_expiring_soon_keys,
    remove_expiry,
    set_expiry,
)

FUTURE = time.time() + 3600  # 1 hour from now
PAST = time.time() - 3600    # 1 hour ago


class TestExpiryRecord:
    def test_to_dict_contains_required_fields(self):
        r = ExpiryRecord(key="DB_PASS", expires_at=FUTURE)
        d = r.to_dict()
        assert "key" in d
        assert "expires_at" in d
        assert "warn_before" in d

    def test_from_dict_roundtrip(self):
        r = ExpiryRecord(key="DB_PASS", expires_at=FUTURE, warn_before=3600)
        assert ExpiryRecord.from_dict(r.to_dict()) == r

    def test_is_expired_future(self):
        r = ExpiryRecord(key="K", expires_at=FUTURE)
        assert not r.is_expired()

    def test_is_expired_past(self):
        r = ExpiryRecord(key="K", expires_at=PAST)
        assert r.is_expired()

    def test_is_expiring_soon_within_window(self):
        soon = time.time() + 60  # 60 seconds from now
        r = ExpiryRecord(key="K", expires_at=soon, warn_before=3600)
        assert r.is_expiring_soon()

    def test_is_expiring_soon_outside_window(self):
        far = time.time() + 7200
        r = ExpiryRecord(key="K", expires_at=far, warn_before=3600)
        assert not r.is_expiring_soon()

    def test_is_expiring_soon_already_expired(self):
        r = ExpiryRecord(key="K", expires_at=PAST, warn_before=9999)
        assert not r.is_expiring_soon()


class TestSetExpiry:
    def test_adds_new_record(self):
        updated = set_expiry({}, "API_KEY", FUTURE)
        assert "API_KEY" in updated
        assert updated["API_KEY"].expires_at == FUTURE

    def test_overwrites_existing_record(self):
        records = set_expiry({}, "API_KEY", FUTURE)
        new_future = FUTURE + 3600
        records = set_expiry(records, "API_KEY", new_future)
        assert records["API_KEY"].expires_at == new_future

    def test_empty_key_raises(self):
        with pytest.raises(ExpiryError, match="empty"):
            set_expiry({}, "", FUTURE)

    def test_past_timestamp_raises(self):
        with pytest.raises(ExpiryError, match="future"):
            set_expiry({}, "K", PAST)


class TestRemoveExpiry:
    def test_removes_existing_key(self):
        records = set_expiry({}, "TOKEN", FUTURE)
        updated = remove_expiry(records, "TOKEN")
        assert "TOKEN" not in updated

    def test_remove_missing_key_raises(self):
        with pytest.raises(ExpiryError, match="No expiry record"):
            remove_expiry({}, "MISSING")


class TestGetExpiredKeys:
    def test_returns_expired(self):
        records = {
            "OLD": ExpiryRecord(key="OLD", expires_at=PAST),
            "NEW": ExpiryRecord(key="NEW", expires_at=FUTURE),
        }
        expired = get_expired_keys(records)
        assert len(expired) == 1
        assert expired[0].key == "OLD"

    def test_empty_records_returns_empty(self):
        assert get_expired_keys({}) == []


class TestGetExpiringSoonKeys:
    def test_returns_expiring_soon(self):
        soon = time.time() + 100
        records = {
            "SOON": ExpiryRecord(key="SOON", expires_at=soon, warn_before=3600),
            "SAFE": ExpiryRecord(key="SAFE", expires_at=FUTURE + 7200, warn_before=60),
        }
        result = get_expiring_soon_keys(records)
        assert len(result) == 1
        assert result[0].key == "SOON"
