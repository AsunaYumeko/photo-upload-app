"""Upload Service module for Photo Upload App.

This module handles HTTP communication with the PDA server API.
"""

import requests
import base64
from typing import Optional, List
from models import UploadResult


class UploadService:
    """上传服务 - Handles PDA image upload and sign-off API."""
    
    DEFAULT_TIMEOUT = 30  # seconds
    USERNAME = "jingpin"
    PASSWORD = "6195593efe9d8515ef85064da94bb2e7"  # MD5 encrypted
    
    def __init__(self, base_url: str):
        """初始化，设置 API 基础地址
        
        Args:
            base_url: Base URL of the API (e.g. http://192.168.100.100:8099)
        """
        self._base_url = base_url.rstrip('/')
    
    def ping(self) -> UploadResult:
        """检查服务状态"""
        try:
            response = requests.get(
                f"{self._base_url}/Image/Ping",
                timeout=self.DEFAULT_TIMEOUT
            )
            if response.status_code == 200:
                return UploadResult(success=True, message="Service OK")
            return UploadResult(success=False, message=f"Service error: {response.status_code}")
        except Exception as e:
            return UploadResult(success=False, message=f"Connection failed: {str(e)}")
    
    def get_tasks(self) -> UploadResult:
        """获取任务列表"""
        try:
            response = requests.get(
                f"{self._base_url}/Image/GetTasks",
                timeout=self.DEFAULT_TIMEOUT
            )
            data = response.json()
            if data.get("StatusCode") == 200:
                return UploadResult(
                    success=True,
                    message="Tasks loaded",
                    response_data=data
                )
            return UploadResult(
                success=False,
                message=data.get("message", "Failed to get tasks")
            )
        except Exception as e:
            return UploadResult(success=False, message=f"Error: {str(e)}")
    
    def update_status(self, order_no: str) -> UploadResult:
        """更新任务状态为处理中"""
        try:
            response = requests.get(
                f"{self._base_url}/Image/UpdateStatus",
                params={"orderNo": order_no},
                timeout=self.DEFAULT_TIMEOUT
            )
            data = response.json()
            if data.get("StatusCode") == 200:
                return UploadResult(success=True, message="Status updated")
            return UploadResult(
                success=False,
                message=data.get("message", "Failed to update status")
            )
        except Exception as e:
            return UploadResult(success=False, message=f"Error: {str(e)}")
    
    def swap_image(self, base64_data: str) -> UploadResult:
        """将Base64图片转换为HTTP链接
        
        Args:
            base64_data: Base64 encoded image data (without prefix)
            
        Returns:
            UploadResult with ImageUrl on success
        """
        try:
            # Add data:image prefix if not present
            if not base64_data.startswith("data:image"):
                base64_data = f"data:image/jpg;base64,{base64_data}"
            
            payload = {
                "username": self.USERNAME,
                "password": self.PASSWORD,
                "imgUrl": base64_data
            }
            
            response = requests.post(
                f"{self._base_url}/Image/Swap",
                json=payload,
                timeout=self.DEFAULT_TIMEOUT,
                headers={"Content-Type": "application/json"}
            )
            
            data = response.json()
            if data.get("StatusCode") == 200:
                return UploadResult(
                    success=True,
                    message="Image converted",
                    response_data={"ImageUrl": data.get("ImageUrl")}
                )
            return UploadResult(
                success=False,
                message=data.get("Message", "Image conversion failed")
            )
        except requests.exceptions.Timeout:
            return UploadResult(success=False, message="Upload timeout")
        except requests.exceptions.ConnectionError:
            return UploadResult(success=False, message="Network unavailable")
        except Exception as e:
            return UploadResult(success=False, message=f"Error: {str(e)}")
    
    def sign_for(self, record_id: str, image_urls: List[str]) -> UploadResult:
        """图片签收
        
        Args:
            record_id: Record ID (order number)
            image_urls: List of HTTP image URLs
            
        Returns:
            UploadResult with sign-off details on success
        """
        try:
            payload = {
                "username": self.USERNAME,
                "password": self.PASSWORD,
                "recordId": record_id,
                "imgUrl": image_urls
            }
            
            response = requests.post(
                f"{self._base_url}/Image/SignFor",
                json=payload,
                timeout=self.DEFAULT_TIMEOUT,
                headers={"Content-Type": "application/json"}
            )
            
            data = response.json()
            if data.get("StatusCode") == 200:
                return UploadResult(
                    success=True,
                    message="Sign-off successful",
                    response_data=data
                )
            return UploadResult(
                success=False,
                message=data.get("Message", "Sign-off failed")
            )
        except requests.exceptions.Timeout:
            return UploadResult(success=False, message="Request timeout")
        except requests.exceptions.ConnectionError:
            return UploadResult(success=False, message="Network unavailable")
        except Exception as e:
            return UploadResult(success=False, message=f"Error: {str(e)}")
    
    def upload_and_sign(self, base64_data: str, record_id: str) -> UploadResult:
        """完整上传流程：转换图片 + 签收
        
        Args:
            base64_data: Base64 encoded image
            record_id: Order/record ID
            
        Returns:
            UploadResult
        """
        # Step 1: Convert image to HTTP URL
        swap_result = self.swap_image(base64_data)
        if not swap_result.success:
            return swap_result
        
        image_url = swap_result.response_data.get("ImageUrl")
        if not image_url:
            return UploadResult(success=False, message="No image URL returned")
        
        # Step 2: Sign for the image
        return self.sign_for(record_id, [image_url])
    
    @property
    def base_url(self) -> str:
        """Get current base URL."""
        return self._base_url
    
    def set_base_url(self, base_url: str) -> None:
        """Update base URL."""
        self._base_url = base_url.rstrip('/')
