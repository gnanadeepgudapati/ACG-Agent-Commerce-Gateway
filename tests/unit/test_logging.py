import json
import logging

from mercora.core.logging import JsonFormatter, request_id_var


def _make_record(message: str, level: int = logging.INFO) -> logging.LogRecord:
    return logging.LogRecord(
        name="mercora.test",
        level=level,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )


def test_formats_as_valid_json_with_expected_fields() -> None:
    formatter = JsonFormatter()
    record = _make_record("hello world")

    parsed = json.loads(formatter.format(record))

    assert parsed["message"] == "hello world"
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "mercora.test"
    assert "timestamp" in parsed


def test_includes_request_id_when_set_in_context() -> None:
    token = request_id_var.set("req-123")
    try:
        formatter = JsonFormatter()
        record = _make_record("with correlation")
        parsed = json.loads(formatter.format(record))
        assert parsed["request_id"] == "req-123"
    finally:
        request_id_var.reset(token)


def test_omits_request_id_when_not_set() -> None:
    formatter = JsonFormatter()
    record = _make_record("no correlation")
    parsed = json.loads(formatter.format(record))
    assert "request_id" not in parsed
