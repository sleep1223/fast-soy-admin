"""Sqids 编解码单元测试。

覆盖点：
- 正整数与 0 的编解码对称性
- 相同 SECRET_KEY 下输出确定性
- 非法 sqid 字符串的解码错误处理
- 编码结果长度满足 min_length 约束
"""

import pytest
from sqids import Sqids

from app.core.config import APP_SETTINGS
from app.core.sqids import _MIN_LENGTH, _derive_alphabet, decode_id, encode_id


def _new_sqids(secret: str) -> Sqids:
    return Sqids(alphabet=_derive_alphabet(secret), min_length=_MIN_LENGTH)


class TestEncodeDecode:
    def test_encode_decode_zero(self):
        encoded = encode_id(0)
        assert isinstance(encoded, str)
        assert decode_id(encoded) == 0

    @pytest.mark.parametrize("value", [1, 42, 10_000, 999_999_999])
    def test_encode_decode_round_trip(self, value: int):
        encoded = encode_id(value)
        assert decode_id(encoded) == value

    def test_encoded_length_at_least_min_length(self):
        """编码结果长度应不小于模块内定义的 _MIN_LENGTH（8）。"""
        assert len(encode_id(0)) >= 8
        assert len(encode_id(1)) >= 8
        assert len(encode_id(10_000_000)) >= 8

    def test_deterministic_output_for_same_secret(self):
        """相同密钥派生出的独立实例应产生一致、可互解的结果。"""
        first = _new_sqids("fixed-test-secret")
        second = _new_sqids("fixed-test-secret")

        encoded = first.encode([12345])
        assert encoded == second.encode([12345])
        assert second.decode(encoded) == [12345]


class TestDecodeErrors:
    def test_decode_empty_string_raises(self):
        with pytest.raises(ValueError, match="invalid sqid"):
            decode_id("")

    def test_decode_invalid_characters_raises(self):
        with pytest.raises(ValueError, match="invalid sqid"):
            decode_id("!!!!@@@@")

    def test_decode_multiple_numbers_raises(self):
        payload = _new_sqids(APP_SETTINGS.SECRET_KEY).encode([1, 2])
        with pytest.raises(ValueError, match="invalid sqid"):
            decode_id(payload)
