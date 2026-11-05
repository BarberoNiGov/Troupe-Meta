import pytest

from app.providers.base import ProviderError
from app.providers.chat import check_truncation, parse_json_object


def test_parses_fenced_json():
    data = parse_json_object('```json\n{"approach":"a","html":"<html></html>"}\n```')
    assert data["approach"] == "a"


def test_tolerates_literal_newline_inside_html_string():
    raw = '{"approach":"plan","html":"<!doctype html>\n<html>\n<body>x</body>\n</html>"}'
    data = parse_json_object(raw)
    assert "<html>" in data["html"]


def test_rejects_non_object():
    with pytest.raises(ProviderError):
        parse_json_object("not json")


def test_truncation_is_reported_before_parsing():
    payload = {"choices": [{"finish_reason": "length", "message": {"content": "{"}}]}
    with pytest.raises(ProviderError, match="output truncated at 48000 tokens"):
        check_truncation(payload, "fake", 48000)


def test_finished_response_is_not_truncated():
    payload = {"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]}
    check_truncation(payload, "fake", 48000)
