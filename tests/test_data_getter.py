from typing import Dict

import pytest

from orca_python import DataGetter


class MockDataGetter(DataGetter[Dict[str, float]]):
    """Simple implementation for testing the ABC."""

    def encode(self, data_struct: dict) -> bytes:
        import json

        return json.dumps(data_struct).encode("utf-8")

    def decode(self, data_bytes: bytes) -> dict:
        import json

        return json.loads(data_bytes.decode("utf-8"))


class BrokenEncodeGetter(DataGetter[str]):
    """Implementation that fails on encode."""

    def encode(self, data_struct: str) -> bytes:
        raise ValueError("Encode failed")

    def decode(self, data_bytes: bytes) -> str:
        return data_bytes.decode("utf-8")


class BrokenDecodeGetter(DataGetter[list]):
    """Implementation that fails on decode."""

    def encode(self, data_struct: list) -> bytes:
        import json

        return json.dumps(data_struct).encode("utf-8")

    def decode(self, data_bytes: bytes) -> list:
        raise ValueError("Decode failed")


def test_data_getter_errors():
    """Test that DataGetter cannot be instantiated directly."""
    with pytest.raises(TypeError):
        DataGetter()


def test_abstract_methods_required():
    """Test that implementing classes must define both abstract methods."""

    class IncompleteGetter(DataGetter[str]):
        def encode(self, data_struct: str) -> bytes:
            return data_struct.encode("utf-8")

        # Missing decode method

    with pytest.raises(TypeError):
        IncompleteGetter()


def test_successful_encode_decode():
    """Test successful round-trip encoding and decoding."""
    getter = MockDataGetter()
    test_data = {"key": "value", "number": 42, "nested": {"inner": "data"}}

    # Test encode
    encoded = getter.encode(test_data)
    assert isinstance(encoded, bytes)
    assert len(encoded) > 0

    # Test decode
    decoded = getter.decode(encoded)
    assert isinstance(decoded, dict)
    assert decoded == test_data


def test_encode_with_empty_data():
    """Test encoding empty data structures."""
    getter = MockDataGetter()

    empty_dict = {}
    encoded = getter.encode(empty_dict)
    decoded = getter.decode(encoded)
    assert decoded == empty_dict


def test_encode_with_complex_data():
    """Test encoding complex nested data structures."""
    getter = MockDataGetter()

    complex_data = {
        "strings": ["hello", "world"],
        "numbers": [1, 2.5, -3],
        "booleans": [True, False],
        "null": None,
        "nested": {"deep": {"very_deep": "value"}},
    }

    encoded = getter.encode(complex_data)
    decoded = getter.decode(encoded)
    assert decoded == complex_data


def test_encode_failure():
    """Test handling of encode failures."""
    getter = BrokenEncodeGetter()

    with pytest.raises(ValueError, match="Encode failed"):
        getter.encode("test data")


def test_decode_failure():
    """Test handling of decode failures."""
    getter = BrokenDecodeGetter()

    with pytest.raises(ValueError, match="Decode failed"):
        getter.decode(b"some bytes")


def test_decode_invalid_bytes():
    """Test decoding invalid byte data."""
    getter = MockDataGetter()

    # Invalid JSON bytes
    with pytest.raises(Exception):  # Could be JSONDecodeError or UnicodeDecodeError
        getter.decode(b"\xff\xfe\x00\x01")


def test_type_consistency():
    """Test that encode input type matches decode output type."""
    getter = MockDataGetter()

    original_data = {"test": "data"}
    encoded = getter.encode(original_data)
    decoded = getter.decode(encoded)

    # Both should be the same type
    assert type(original_data) == type(decoded)
    assert original_data == decoded


def test_multiple_round_trips():
    """Test multiple encode/decode cycles maintain data integrity."""
    getter = MockDataGetter()
    original_data = {"iteration": 0, "data": [1, 2, 3]}

    current_data = original_data
    for i in range(5):
        encoded = getter.encode(current_data)
        current_data = getter.decode(encoded)

    assert current_data == original_data


def test_different_data_sizes():
    """Test encoding/decoding data of various sizes."""
    getter = MockDataGetter()

    # Small data
    small_data = {"a": 1}
    assert getter.decode(getter.encode(small_data)) == small_data

    # Medium data
    medium_data = {f"key_{i}": f"value_{i}" for i in range(100)}
    assert getter.decode(getter.encode(medium_data)) == medium_data

    # Large data
    large_data = {f"key_{i}": f"value_{i}" * 100 for i in range(1000)}
    assert getter.decode(getter.encode(large_data)) == large_data


def test_encoded_bytes_not_empty():
    """Test that encoded data is never empty for non-empty input."""
    getter = MockDataGetter()

    test_cases = [
        {"single": "value"},
        {"multiple": "values", "with": "keys"},
        {"nested": {"data": "structure"}},
    ]

    for data in test_cases:
        encoded = getter.encode(data)
        assert isinstance(encoded, bytes)
        assert len(encoded) > 0


def test_encode_decode_independence():
    """Test that multiple instances don't interfere with each other."""
    getter1 = MockDataGetter()
    getter2 = MockDataGetter()

    data1 = {"first": "instance"}
    data2 = {"second": "instance"}

    encoded1 = getter1.encode(data1)
    encoded2 = getter2.encode(data2)

    # Cross-decode to ensure independence
    decoded1_from_1 = getter1.decode(encoded1)
    decoded2_from_2 = getter2.decode(encoded2)
    decoded1_from_2 = getter2.decode(encoded1)
    decoded2_from_1 = getter1.decode(encoded2)

    assert decoded1_from_1 == data1
    assert decoded2_from_2 == data2
    assert decoded1_from_2 == data1
    assert decoded2_from_1 == data2
