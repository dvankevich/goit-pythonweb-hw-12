import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from src.services.upload_file import UploadFileService


def test_upload_file_service_init():
    """Тестуємо правильність ініціалізації налаштувань Cloudinary (__init__)"""
    # Мокаємо settings, щоб не залежати від реальних змінних оточення
    with (
        patch("src.services.upload_file.settings") as mock_settings,
        patch("src.services.upload_file.cloudinary.config") as mock_config,
    ):

        # Налаштовуємо фейкові значення для settings
        mock_settings.CLD_NAME = "test_cloud_name"
        mock_settings.CLD_API_KEY = "test_api_key"
        # Мокаємо get_secret_value() для SecretStr
        mock_settings.CLD_API_SECRET.get_secret_value.return_value = "test_api_secret"

        # Створюємо екземпляр сервісу
        service = UploadFileService()

        # Перевіряємо, чи був викликаний cloudinary.config з правильними параметрами
        mock_config.assert_called_once_with(
            cloud_name="test_cloud_name",
            api_key="test_api_key",
            api_secret="test_api_secret",
            secure=True,
        )
        assert service.cloud_name == "test_cloud_name"


def test_upload_file_success():
    """Тестуємо успішне завантаження файлу та генерацію URL"""
    mock_file = MagicMock()
    mock_file.file = b"fake_file_bytes"  # Імітуємо атрибут file з UploadFile
    username = "testuser"

    with (
        patch("src.services.upload_file.cloudinary.uploader.upload") as mock_upload,
        patch(
            "src.services.upload_file.cloudinary.CloudinaryImage"
        ) as mock_image_class,
    ):

        # Налаштовуємо повернення результату від uploader.upload
        mock_upload.return_value = {"version": "1234567890"}

        # Налаштовуємо мойн класу CloudinaryImage та його методу build_url
        mock_image_instance = MagicMock()
        mock_image_class.return_value = mock_image_instance
        mock_image_instance.build_url.return_value = (
            "https://res.cloudinary.com/fake_url/avatar.jpg"
        )

        # Викликаємо статичний метод
        result_url = UploadFileService.upload_file(mock_file, username)

        # 1. Перевіряємо, що повернувся правильний URL
        assert result_url == "https://res.cloudinary.com/fake_url/avatar.jpg"

        # 2. Перевіряємо, що upload викликався з правильними параметрами
        mock_upload.assert_called_once_with(
            mock_file.file,
            public_id=f"RestApp/{username}",
            overwrite=True,
            resource_type="image",
        )

        # 3. Перевіряємо, що CloudinaryImage викликався правильно
        mock_image_class.assert_called_once_with(f"RestApp/{username}")
        mock_image_instance.build_url.assert_called_once_with(
            width=250, height=250, crop="fill", version="1234567890"
        )


def test_upload_file_exception():
    """Тестуємо перехоплення помилки Cloudinary і виклик HTTPException (рядки 42-47)"""
    mock_file = MagicMock()
    username = "testuser"

    with patch("src.services.upload_file.cloudinary.uploader.upload") as mock_upload:
        # Імітуємо падіння Cloudinary
        mock_upload.side_effect = Exception("Cloudinary connection timeout")

        # Перевіряємо, що наш сервіс перехоплює Exception і генерує HTTPException 500
        with pytest.raises(HTTPException) as exc_info:
            UploadFileService.upload_file(mock_file, username)

        assert exc_info.value.status_code == 500
        assert "Failed to upload avatar" in exc_info.value.detail
