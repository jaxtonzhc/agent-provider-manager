"""Tests for agents/base.py helpers."""

from __future__ import annotations

from apm.agents.base import is_port_open, yaml_get, yaml_set


class TestYamlGet:
    def test_get_existing_key(self):
        text = "model:\n  default: mimo-v2.5-pro\n  base_url: https://api.test.com\n"
        assert yaml_get(text, "model", "default") == "mimo-v2.5-pro"
        assert yaml_get(text, "model", "base_url") == "https://api.test.com"

    def test_get_missing_key(self):
        text = "model:\n  default: test\n"
        assert yaml_get(text, "model", "nonexistent") is None

    def test_get_missing_section(self):
        text = "other:\n  key: value\n"
        assert yaml_get(text, "model", "key") is None

    def test_get_quoted_value(self):
        text = 'model:\n  default: "quoted-value"\n'
        assert yaml_get(text, "model", "default") == "quoted-value"

    def test_get_single_quoted_value(self):
        text = "model:\n  default: 'single-quoted'\n"
        assert yaml_get(text, "model", "default") == "single-quoted"

    def test_get_stops_at_next_section(self):
        text = "model:\n  key: value1\nother:\n  key: value2\n"
        assert yaml_get(text, "model", "key") == "value1"
        assert yaml_get(text, "other", "key") == "value2"


class TestYamlSet:
    def test_set_existing_key(self):
        text = "model:\n  default: old-value\n  base_url: https://old.com\n"
        result = yaml_set(text, "model", "default", "new-value")
        assert "default: new-value" in result
        assert "old-value" not in result

    def test_set_preserves_other_keys(self):
        text = "model:\n  default: val1\n  base_url: https://test.com\n"
        result = yaml_set(text, "model", "default", "new-val")
        assert "base_url: https://test.com" in result

    def test_set_adds_new_key(self):
        text = "model:\n  default: val\n"
        result = yaml_set(text, "model", "new_key", "new_val")
        assert "new_key: new_val" in result

    def test_set_adds_key_to_existing_section(self):
        text = "model:\n  existing: val\n"
        result = yaml_set(text, "model", "new_key", "new_val")
        assert "new_key: new_val" in result
        assert "existing: val" in result


class TestIsPortOpen:
    def test_closed_port(self):
        # Use a port that's very likely closed
        assert is_port_open(59999, timeout=0.1) is False

    def test_open_port(self):
        import socket

        # Start a temporary server
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        try:
            assert is_port_open(port, timeout=0.5) is True
        finally:
            server.close()
