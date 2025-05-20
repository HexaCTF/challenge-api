import pytest
from challenge_api.exceptions.common import EmptyValueException

class TestCommonException:
    def test_error_message(self):
        e = EmptyValueException("Something went wrong")
        assert e.error_msg == "Something went wrong"

    def test_dynamic_attribute_set_and_get(self):
        e = EmptyValueException("Dynamic attr test")
        e.username = "hwans"
        e.status_code = 500
        assert e.username == "hwans"
        assert e.status_code == 500

    def test_attribute_overwrite(self):
        e = EmptyValueException("Test")
        e.key = "initial"
        e.key = "updated"
        assert e.key == "updated"

    def test_attribute_delete(self):
        e = EmptyValueException("Delete test")
        e.token = "secret"
        del e.token
        with pytest.raises(AttributeError):
            _ = e.token

    def test_nonexistent_attribute_access(self):
        e = EmptyValueException("Missing attr")
        with pytest.raises(AttributeError):
            _ = e.not_set

    def test_str_output(self):
        e = EmptyValueException("Testing __str__")
        e.user = "admin"
        e.code = 403
        result = str(e)
        assert "EmptyValueException" in result
        assert "'user': 'admin'" in result
        assert "'code': 403" in result
