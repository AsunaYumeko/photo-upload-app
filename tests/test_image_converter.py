"""Unit tests for ImageConverter module."""

import os
import pytest

from src.image_converter import ImageConverter, Result


class TestImageConverterEncode:
    """Tests for encode_to_base64 method."""
    
    def test_encode_valid_image(self, tmp_path):
        """Test encoding a valid image file."""
        # Create a test image file
        image_path = tmp_path / "test.png"
        image_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"test data")
        
        result = ImageConverter.encode_to_base64(str(image_path))
        
        assert result.success is True
        assert len(result.value) > 0
        # Base64 string should only contain valid characters
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" 
                   for c in result.value)
    
    def test_encode_nonexistent_file(self):
        """Test encoding a file that doesn't exist."""
        result = ImageConverter.encode_to_base64("/nonexistent/path/image.png")
        
        assert result.success is False
        assert "not found" in result.value.lower()
    
    def test_encode_empty_path(self):
        """Test encoding with empty path."""
        result = ImageConverter.encode_to_base64("")
        
        assert result.success is False
        assert "empty" in result.value.lower()


class TestImageConverterDecode:
    """Tests for decode_from_base64 method."""
    
    def test_decode_valid_base64(self, tmp_path):
        """Test decoding valid Base64 string."""
        # Simple test data
        original_data = b"test image data"
        base64_string = ImageConverter.encode_bytes_to_base64(original_data)
        output_path = str(tmp_path / "decoded.bin")
        
        result = ImageConverter.decode_from_base64(base64_string, output_path)
        
        assert result.success is True
        assert os.path.exists(output_path)
        with open(output_path, "rb") as f:
            assert f.read() == original_data
    
    def test_decode_empty_string(self, tmp_path):
        """Test decoding empty Base64 string."""
        output_path = str(tmp_path / "output.bin")
        result = ImageConverter.decode_from_base64("", output_path)
        
        assert result.success is False
        assert "empty" in result.value.lower()
    
    def test_decode_empty_output_path(self):
        """Test decoding with empty output path."""
        result = ImageConverter.decode_from_base64("dGVzdA==", "")
        
        assert result.success is False
        assert "empty" in result.value.lower()
