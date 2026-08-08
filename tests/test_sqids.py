"""Sqids 编解码单元测试。

覆盖点：
- 正整数与 0 的编解码对称性
- 相同 SECRET_KEY 下输出确定性
- 非法 sqid 字符串的解码错误处理
- 编码结果长度满足 min_length 约束
"""

import pytest

from app.core.sqids import decode_id, encode_id


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
        """同一实例/同一 SECRET_KEY 对同一数字应产出相同 sqid。"""
        assert encode_id(12345) == encode_id(12345)


class TestDecodeErrors:
    def test_decode_empty_string_raises(self):
        with pytest.raises(ValueError, match="invalid sqid"):
            decode_id("")

    def test_decode_invalid_characters_raises(self):
        with pytest.raises(ValueError, match="invalid sqid"):
            decode_id("!!!!@@@@")

    def test_decode_gibberish_raises(self):
        with pytest.raises(ValueError, match="invalid sqid"):
            decode_id("not-a-valid-sqid")
