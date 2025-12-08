"""Property-based tests for Photo Upload App.

Uses Hypothesis library for property-based testing.
"""

import pytest
from hypothesis import given, settings, strategies as st

from src.image_converter import ImageConverter


class TestBase64RoundTrip:
    """
    **Feature: photo-upload-app, Property 1: Base64 Round-Trip Consistency**
    
    *For any* valid image byte sequence, encoding to Base64 and then 
    decoding back to bytes SHALL produce the original byte sequence.
    
    **Validates: Requirements 2.1, 2.2, 2.3**
    """
    
    @given(st.binary(min_size=1, max_size=10000))
    @settings(max_examples=100)
    def test_base64_round_trip_consistency(self, data: bytes):
        """Property: encode(decode(x)) == x for any byte sequence."""
        # Encode bytes to Base64
        encoded = ImageConverter.encode_bytes_to_base64(data)
        
        # Decode Base64 back to bytes
        decoded = ImageConverter.decode_base64_to_bytes(encoded)
        
        # Verify round-trip produces original data
        assert decoded == data, (
            f"Round-trip failed: original {len(data)} bytes != decoded {len(decoded)} bytes"
        )
