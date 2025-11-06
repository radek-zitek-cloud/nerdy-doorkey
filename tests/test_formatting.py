from datetime import datetime

from src.nedok.formatting import format_size, format_timestamp


def test_format_size_scales_units():
    assert format_size(512) == "512B"
    assert format_size(1024) == "1K"
    assert format_size(1536) == "1.5K"
    assert format_size(1048576) == "1M"


def test_format_timestamp_short_format():
    timestamp = datetime(2024, 1, 2, 13, 45)
    assert format_timestamp(timestamp) == "Jan 02 13:45"
