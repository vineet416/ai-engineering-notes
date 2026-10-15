# base62 on its own, no HTTP.
import pytest

from app.core.config import ID_OFFSET
from app.services.codes import ALPHABET, decode, encode


def test_small_numbers():
    assert encode(0) == "0"
    assert encode(61) == "Z"
    assert encode(62) == "10"


def test_round_trip():
    for n in [1, 62, 3843, 999_999, 56_800_235_583]:
        assert decode(encode(n)) == n


def test_seven_chars_is_trillions_of_codes():
    assert len(encode(62**7 - 1)) == 7
    assert 62**7 > 3_500_000_000_000


def test_offset_makes_codes_six_chars():
    assert len(encode(1 + ID_OFFSET)) == 6


def test_only_url_safe_characters():
    assert set(encode(123_456_789_012)) <= set(ALPHABET)


def test_negative_not_allowed():
    with pytest.raises(ValueError):
        encode(-1)


def test_no_collisions_for_100k_ids():
    codes = {encode(i + ID_OFFSET) for i in range(1, 100_001)}
    assert len(codes) == 100_000
