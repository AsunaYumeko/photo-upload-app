"""Main application module for Photo Upload App.

This is the entry point for the Kivy application.
"""

import os
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, BooleanProperty, ListProperty
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.text import LabelBase
from camera_module import CameraModule
from image_converter import ImageConverter
from upload_service import UploadService
from config_storage import ConfigStorage
from permission_manager import PermissionManager
from models import AppConfig, PhotoData


# Get the directory where this file is located
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")

# Register Chinese font
FONT_PATH = os.path.join(APP_DIR, "fonts", "msyh.ttc")
if os.path.exists(FONT_PATH):
    LabelBase.register(name='Chinese', fn_regular=FONT_PATH)

# Use app private directory for photos (works on Android)
def get_photos_dir():
    """Get photos directory that works on Android."""
    try:
        from android import mActivity
        # Use app's external files directory on Android
        context = mActivity.getApplicationContext()
        files_dir = context.getExternalFilesDir(None)
        if files_dir:
            photos_dir = os.path.join(files_dir.getAbsolutePath(), 'photos')
        else:
            photos_dir = os.path.join(APP_DIR, "photos")
    except ImportError:
        # Not on Android, use local directory
        photos_dir = os.path.join(APP_DIR, "photos")
    
    if not os.path.exists(photos_dir):
        try:
            os.makedirs(photos_dir)
        except Exception:
            pass
    return photos_dir

PHOTOS_DIR = get_photos_dir()

# Load the KV file
Builder.load_file(os.path.join(APP_DIR, "photoupload.kv"))


class MainScreen(Screen):
    """Main screen with task list and photo capture"""
    
    current_photo_path = StringProperty("")
    current_base64 = StringProperty("")
    current_order_no = StringProperty("")
    is_uploading = BooleanProperty(False)
    image_urls = ListProperty([])  # Store converted image URLs
    photo_paths = ListProperty([])  # Store local photo paths for preview
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._camera = CameraModule(PHOTOS_DIR)
        self._upload_service = None
        self._config_storage = ConfigStorage(CONFIG_PATH)
        self._tasks = []
    
    def on_enter(self):
        """Called when screen is displayed."""
        self._load_config()
    
    def _load_config(self):
        """Load configuration and initialize upload service."""
        config = self._config_storage.load()
        if config.api_url:
            self._upload_service = UploadService(config.api_url)
    
    def refresh_tasks(self):
        """Refresh task list from server"""
        if not self._upload_service:
            self.show_notification("请先配置服务器", is_error=True)
            return
        
        self.show_notification("正在加载...")
        Clock.schedule_once(lambda dt: self._do_refresh_tasks(), 0.1)
    
    def _do_refresh_tasks(self):
        """Perform task refresh"""
        result = self._upload_service.get_tasks()
        if result.success:
            self._tasks = result.response_data.get("tasks", [])
            self._update_task_list()
            self.show_notification(f"已加载 {len(self._tasks)} 个任务")
        else:
            self.show_notification("加载失败", is_error=True)
    
    def _update_task_list(self):
        """Update task list UI"""
        from kivy.metrics import dp
        task_container = self.ids.task_container
        task_container.clear_widgets()
        
        for task in self._tasks:
            btn = Button(
                text=f"{task.get('orderNo', '')} - {task.get('lockerNo', '')}",
                size_hint_y=None,
                height=dp(50),
                font_size='20sp'
            )
            btn.bind(on_release=lambda x, t=task: self.select_task(t))
            task_container.add_widget(btn)
    
    def select_task(self, task):
        """Select a task for processing"""
        self.current_order_no = task.get("orderNo", "")
        self.image_urls = []  # Reset image list
        self.photo_paths = []  # Reset photo paths
        self._update_photo_list()
        self._update_label(self.ids.order_label, f"订单: {self.current_order_no}")
        self._update_label(self.ids.photo_count_label, "照片: 0")
        self.show_notification(f"已选择: {self.current_order_no}")
        
        # Update status to processing
        if self._upload_service:
            self._upload_service.update_status(self.current_order_no)
    
    def capture_photo(self):
        """Trigger photo capture"""
        if not self.current_order_no:
            self.show_notification("请先选择任务", is_error=True)
            return
        
        if not self._camera.is_available():
            self.show_notification("相机不可用", is_error=True)
            return
        
        self.show_notification("正在打开相机...")
        self._camera.capture(self._on_photo_captured)
    
    def _on_photo_captured(self, photo_path):
        """Callback when photo is captured."""
        if not photo_path:
            error = self._camera.get_last_error()
            msg = f"拍照失败: {error}" if error else "拍照失败"
            self.show_notification(msg, is_error=True)
            return
        
        self.current_photo_path = photo_path
        
        # Convert to Base64
        result = ImageConverter.encode_to_base64(photo_path)
        if result.success:
            self.current_base64 = result.value
            self.show_notification("正在上传...")
            # Auto-convert to HTTP URL
            Clock.schedule_once(lambda dt: self._convert_image(photo_path), 0.1)
        else:
            self.show_notification("编码失败", is_error=True)
    
    def _convert_image(self, photo_path=None):
        """Convert base64 image to HTTP URL via Swap API"""
        import time
        if not self._upload_service:
            self.show_notification("未配置服务器", is_error=True)
            return
        
        # Generate filename with order number and timestamp (no extension)
        timestamp = int(time.time() * 1000)
        photo_num = len(self.image_urls) + 1
        filename = f"{self.current_order_no}_{photo_num}_{timestamp}"
        
        result = self._upload_service.swap_image(self.current_base64, filename)
        if result.success:
            image_url = result.response_data.get("ImageUrl")
            if image_url:
                self.image_urls.append(image_url)
                if photo_path:
                    self.photo_paths.append(photo_path)
                self._update_photo_list()
                self._update_label(self.ids.photo_count_label, f"照片: {len(self.image_urls)}")
                self.show_notification(f"第 {len(self.image_urls)} 张已就绪")
            else:
                self.show_notification("上传失败", is_error=True)
        else:
            self.show_notification("上传失败", is_error=True)
    
    def submit_sign(self):
        """Submit all photos for sign-off"""
        if not self.current_order_no:
            self.show_notification("请先选择任务", is_error=True)
            return
        
        if not self.image_urls:
            self.show_notification("请先拍照", is_error=True)
            return
        
        if not self._upload_service:
            self.show_notification("未配置服务器", is_error=True)
            return
        
        self.is_uploading = True
        self._show_loading(True)
        self.show_notification("正在提交...")
        Clock.schedule_once(lambda dt: self._do_sign(), 0.1)
    
    def _do_sign(self):
        """Perform sign-off"""
        num_photos = len(self.image_urls)
        result = self._upload_service.sign_for(self.current_order_no, list(self.image_urls))
        
        self.is_uploading = False
        self._show_loading(False)
        
        if result.success:
            self.show_notification("签收成功!", is_error=False)
            # Reset state
            self.current_order_no = ""
            self.current_base64 = ""
            self.image_urls = []
            self.photo_paths = []
            self._update_photo_list()
            self._update_label(self.ids.order_label, "订单: 无")
            self._update_label(self.ids.photo_count_label, "照片: 0")
            # Delay refresh so user can see success message
            Clock.schedule_once(lambda dt: self.refresh_tasks(), 2.0)
        else:
            self.show_notification("签收失败", is_error=True)
    
    def _update_photo_list(self):
        """Update photo preview list"""
        from kivy.metrics import dp
        photo_container = self.ids.photo_container
        photo_container.clear_widgets()
        
        for i, path in enumerate(self.photo_paths):
            # Create a box for each photo with delete button
            photo_box = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(120),
                spacing=dp(10)
            )
            
            # Photo image (clickable)
            img = Image(
                source=path,
                allow_stretch=True,
                keep_ratio=True,
                size_hint_x=0.7
            )
            
            # Delete button
            del_btn = Button(
                text='删除',
                font_name='Chinese',
                size_hint_x=0.3,
                font_size='16sp',
                background_color=(0.8, 0.2, 0.2, 1)
            )
            del_btn.bind(on_release=lambda x, idx=i: self._confirm_delete_photo(idx))
            
            photo_box.add_widget(img)
            photo_box.add_widget(del_btn)
            photo_container.add_widget(photo_box)
    
    def _confirm_delete_photo(self, index):
        """Show confirmation popup for deleting photo"""
        from kivy.metrics import dp
        
        content = BoxLayout(orientation='vertical', spacing=dp(20), padding=dp(20))
        content.add_widget(Label(
            text=f'确定删除第 {index + 1} 张照片?',
            font_name='Chinese',
            font_size='18sp'
        ))
        
        btn_box = BoxLayout(spacing=dp(20), size_hint_y=None, height=dp(60))
        
        confirm_btn = Button(
            text='确定',
            font_name='Chinese',
            background_color=(0.8, 0.2, 0.2, 1)
        )
        cancel_btn = Button(
            text='取消',
            font_name='Chinese',
            background_color=(0.5, 0.5, 0.5, 1)
        )
        
        btn_box.add_widget(confirm_btn)
        btn_box.add_widget(cancel_btn)
        content.add_widget(btn_box)
        
        popup = Popup(
            title='删除确认',
            title_font='Chinese',
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False
        )
        
        confirm_btn.bind(on_release=lambda x: self._delete_photo(index, popup))
        cancel_btn.bind(on_release=popup.dismiss)
        
        popup.open()
    
    def _delete_photo(self, index, popup):
        """Delete photo at index"""
        popup.dismiss()
        
        if 0 <= index < len(self.photo_paths):
            del self.photo_paths[index]
            del self.image_urls[index]
            self._update_photo_list()
            self._update_label(self.ids.photo_count_label, f"照片: {len(self.image_urls)}")
            self.show_notification(f"已删除第 {index + 1} 张照片")
    
    def _update_label(self, label, text, min_width=25):
        """Update label text with forced refresh to prevent overlap"""
        # Pad text to minimum width to ensure full coverage
        padded_text = text.ljust(min_width)
        # Clear and force redraw
        label.text = ' ' * min_width
        label.texture_update()
        label.canvas.ask_update()
        # Set new text
        label.text = padded_text
        label.texture_update()
        label.canvas.ask_update()
    
    def show_notification(self, message: str, is_error: bool = False):
        """Show notification message"""
        label = self.ids.status_label
        label.color = (1, 0.4, 0.4, 1) if is_error else (0.4, 1, 0.4, 1)
        self._update_label(label, message)
    
    def _show_loading(self, show: bool):
        """Show or hide loading indicator."""
        self.ids.loading_bar.opacity = 1 if show else 0
        self.ids.loading_bar.value = 50 if show else 0


class SettingsScreen(Screen):
    """Settings screen for API configuration"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._config_storage = ConfigStorage(CONFIG_PATH)
    
    def on_enter(self):
        """Called when screen is displayed."""
        self.load_config()
    
    def load_config(self):
        """Load current configuration"""
        config = self._config_storage.load()
        self.ids.api_url_input.text = config.api_url
        self.ids.validation_label.text = ""
    
    def save_config(self):
        """Save configuration"""
        api_url = self.ids.api_url_input.text.strip()
        
        if api_url and not ConfigStorage.validate_url(api_url):
            self.ids.validation_label.text = "Invalid URL"
            return False
        
        config = AppConfig(api_url=api_url)
        if self._config_storage.save(config):
            self.ids.validation_label.color = (0, 0.5, 0, 1)
            self.ids.validation_label.text = "Saved"
            return True
        else:
            self.ids.validation_label.text = "Save failed"
            return False
    
    def test_connection(self):
        """Test API connection"""
        api_url = self.ids.api_url_input.text.strip()
        if not api_url:
            self.ids.validation_label.text = "Enter URL"
            return
        
        self.ids.validation_label.text = "Testing..."
        service = UploadService(api_url)
        result = service.ping()
        
        if result.success:
            self.ids.validation_label.color = (0, 0.5, 0, 1)
            self.ids.validation_label.text = "Connected!"
        else:
            self.ids.validation_label.color = (1, 0, 0, 1)
            self.ids.validation_label.text = result.message


class PhotoUploadApp(App):
    """Main application class"""
    
    def build(self):
        """Build application UI"""
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(SettingsScreen(name='settings'))
        return sm
    
    def on_start(self):
        """Request permissions on app start"""
        PermissionManager.request_all_permissions(self._on_permissions_result)
    
    def _on_permissions_result(self, granted: bool):
        """Handle permission request result."""
        if not granted:
            main_screen = self.root.get_screen('main')
            main_screen.show_notification(
                "Permissions required",
                is_error=True
            )


def main():
    """Application entry point."""
    PhotoUploadApp().run()


if __name__ == '__main__':
    main()
