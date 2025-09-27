import pytest

from orca_python.envs import (
    _parse_connection_string,
)


@pytest.mark.parametrize(
    "connection_string,expected_address,expected_port",
    [
        ("localhost:8080", "localhost", 8080),
        ("192.168.1.1:443", "192.168.1.1", 443),
        ("api.service.com:9000", "api.service.com", 9000),
        ("::1:3000", "::1", 3000),
        ("127.0.0.1:1", "127.0.0.1", 1),
        ("multiple:slashes:here:8080", "multiple:slashes:here", 8080),
    ],
)
def test_parse_connection_string_parametrized_valid(
    connection_string, expected_address, expected_port
):
    """Test for valid connection strings"""
    result = _parse_connection_string(connection_string)
    assert result == (expected_address, expected_port)


@pytest.mark.parametrize(
    "invalid_connection_string",
    [
        "localhost/8080",
        "localhost:",
        ":8080",
        "localhost:abc",
        "localhost:8080/:extra",
        "",
        "no-port",
        " localhost:8080",
        "localhost:8080 ",
    ],
)
def test_parse_connection_string_parametrized_invalid(invalid_connection_string):
    """Test for invalid connection strings"""
    result = _parse_connection_string(invalid_connection_string)
    assert result is None


def test_parse_connection_string_edge_case_port_zero():
    """Test parsing with port zero"""
    result = _parse_connection_string("localhost:0")
    assert result == ("localhost", 0)


def test_parse_connection_string_edge_case_very_long_address():
    """Test parsing with very long address"""
    long_address = "a" * 100 + ".example.com"
    result = _parse_connection_string(f"{long_address}:8080")
    assert result == (long_address, 8080)
