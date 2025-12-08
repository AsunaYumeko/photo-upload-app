"""Image Converter module for Photo Upload App.

This module handles conversion between image files and Base64 encoding.
"""

import base64
import os
from dataclasses import dataclass
from typing import Union


@dataclass
class Result:
    """Result type for operations that can succeed or fail.
    
    Attributes:
        success: Whether the operation succeeded.
        value: The result value on success, or error message on failure.
    """
    success: bool
    value: str


class ImageConverter:
    """图片转换器 - Handles image to Base64 conversion and vice versa."""
    
    @staticmethod
    def encode_to_base64(image_path: str) -> Result:
        """将图片文件编码为 Base64 字符串
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            Result: Success with Base64 string, or failure with error message.
        """
        if not image_path:
            return Result(success=False, value="Image path cannot be empty")
        
        if not os.path.exists(image_path):
            return Result(success=False, value=f"File not found: {image_path}")
        
        try:
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                
            if not image_data:
                return Result(success=False, value="File is empty")
            
            base64_string = base64.b64encode(image_data).decode("utf-8")
            return Result(success=True, value=base64_string)
            
        except PermissionError:
            return Result(success=False, value=f"Permission denied: {image_path}")
        except IOError as e:
            return Result(success=False, value=f"Failed to read file: {str(e)}")
    
    @staticmethod
    def decode_from_base64(base64_string: str, output_path: str) -> Result:
        """将 Base64 字符串解码为图片文件
        
        Args:
            base64_string: Base64 encoded string.
            output_path: Path where the decoded image will be saved.
            
        Returns:
            Result: Success with output path, or failure with error message.
        """
        if not base64_string:
            return Result(success=False, value="Base64 string cannot be empty")
        
        if not output_path:
            return Result(success=False, value="Output path cannot be empty")
        
        try:
            image_data = base64.b64decode(base64_string)
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            with open(output_path, "wb") as output_file:
                output_file.write(image_data)
            
            return Result(success=True, value=output_path)
            
        except base64.binascii.Error as e:
            return Result(success=False, value=f"Invalid Base64 string: {str(e)}")
        except PermissionError:
            return Result(success=False, value=f"Permission denied: {output_path}")
        except IOError as e:
            return Result(success=False, value=f"Failed to write file: {str(e)}")
    
    @staticmethod
    def encode_bytes_to_base64(data: bytes) -> str:
        """Encode raw bytes to Base64 string.
        
        Args:
            data: Raw bytes to encode.
            
        Returns:
            Base64 encoded string.
        """
        return base64.b64encode(data).decode("utf-8")
    
    @staticmethod
    def decode_base64_to_bytes(base64_string: str) -> bytes:
        """Decode Base64 string to raw bytes.
        
        Args:
            base64_string: Base64 encoded string.
            
        Returns:
            Decoded bytes.
        """
        return base64.b64decode(base64_string)
