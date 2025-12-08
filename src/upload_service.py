"""Upload Service module for Photo Upload App.

This module handles HTTP communication with the remote API.
"""

import requests
from typing import Optional

from src.models import UploadResult


class UploadService:
    """上传服务 - Handles image upload to remote API."""
    
    DEFAULT_TIMEOUT = 30  # seconds
    
    def __init__(self, api_url: str):
        """初始化，设置 API 端点
        
        Args:
            api_url: URL of the API endpoint.
        """
        self._api_url = api_url
    
    def upload_image(self, base64_data: str, filename: str = "photo.jpg") -> UploadResult:
        """上传 Base64 编码的图片
        
        Args:
            base64_data: Base64 encoded image data.
            filename: Name of the file being uploaded.
            
        Returns:
            UploadResult: Result of the upload operation.
        """
        if not self._api_url:
            return UploadResult(
                success=False,
                message="API URL 未配置"
            )
        
        if not base64_data:
            return UploadResult(
                success=False,
                message="图片数据为空"
            )
        
        try:
            payload = {
                "image": base64_data,
                "filename": filename
            }
            
            response = requests.post(
                self._api_url,
                json=payload,
                timeout=self.DEFAULT_TIMEOUT,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                try:
                    response_data = response.json()
                except ValueError:
                    response_data = {"raw": response.text}
                
                return UploadResult(
                    success=True,
                    message="上传成功",
                    response_data=response_data
                )
            else:
                error_message = f"服务器错误: {response.status_code}"
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_message = error_data["message"]
                    elif "error" in error_data:
                        error_message = error_data["error"]
                except ValueError:
                    if response.text:
                        error_message = response.text[:200]
                
                return UploadResult(
                    success=False,
                    message=error_message
                )
                
        except requests.exceptions.Timeout:
            return UploadResult(
                success=False,
                message="上传超时，请重试"
            )
        except requests.exceptions.ConnectionError:
            return UploadResult(
                success=False,
                message="网络连接不可用，请检查网络设置"
            )
        except requests.exceptions.RequestException as e:
            return UploadResult(
                success=False,
                message=f"上传失败: {str(e)}"
            )
    
    def set_api_url(self, api_url: str) -> None:
        """更新 API 端点
        
        Args:
            api_url: New API endpoint URL.
        """
        self._api_url = api_url
    
    @property
    def api_url(self) -> str:
        """Get current API URL."""
        return self._api_url
