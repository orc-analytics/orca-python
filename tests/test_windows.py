import pytest

from orca_python import WindowType, MetadataField
from orca_python.exceptions import InvalidWindowArgument, InvalidMetadataFieldArgument


def test_metadata_fields():
    with pytest.raises(InvalidMetadataFieldArgument):
        MetadataField(name="", description="test description")

    with pytest.raises(InvalidMetadataFieldArgument):
        MetadataField(name="test name", description="")

    with pytest.raises(InvalidMetadataFieldArgument):
        MetadataField(name="", description="")

    MetadataField(name="test name", description="test description")


def test_window_type_definition():
    with pytest.raises(InvalidWindowArgument):
        WindowType(
            name="TestWindow",
            version="1.0.0",
            description="test description",
            metadataFields=[
                MetadataField(name="testName", description="test description"),
                MetadataField(name="testName", description="test description"),
            ],
        )
    WindowType(
        name="TestWindow",
        version="1.0.0",
        description="test description",
        metadataFields=[
            MetadataField(name="test name", description="test description")
        ],
    )
