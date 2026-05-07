import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from src.services.upload_file import UploadFileService


def test_upload_file_service_init():
    """Test correct initialization of Cloudinary settings (__init__)"""
    # Mock settings to avoid dependency on real environment variables
    with (
        patch("src.services.upload_file.settings") as mock_settings,
        patch("src.services.upload_file.cloudinary.config") as mock_config,
    ):

        # Set up fake values for settings
        mock_settings.CLD_NAME = "test_cloud_name"
        mock_settings.CLD_API_KEY = "test_api_key"
        # Mock get_secret_value() for SecretStr
        mock_settings.CLD_API_SECRET.get_secret_value.return_value = "test_api_secret"

        # Create service instance
        service = UploadFileService()

        # Check if cloudinary.config was called with correct parameters
        mock_config.assert_called_once_with(
            cloud_name="test_cloud_name",
            api_key="test_api_key",
            api_secret="test_api_secret",
            secure=True,
        )
        assert service.cloud_name == "test_cloud_name"


def test_upload_file_success():
    """Test successful file upload and URL generation"""
    mock_file = MagicMock()
    mock_file.file = b"fake_file_bytes"  # Simulate file attribute from UploadFile
    username = "testuser"

    with (
        patch("src.services.upload_file.cloudinary.uploader.upload") as mock_upload,
        patch(
            "src.services.upload_file.cloudinary.CloudinaryImage"
        ) as mock_image_class,
    ):

        # Set up return result from uploader.upload
        mock_upload.return_value = {"version": "1234567890"}

        # Set up mock of CloudinaryImage class and its build_url method
        mock_image_instance = MagicMock()
        mock_image_class.return_value = mock_image_instance
        mock_image_instance.build_url.return_value = (
            "https://res.cloudinary.com/fake_url/avatar.jpg"
        )

        # Call static method
        result_url = UploadFileService.upload_file(mock_file, username)

        # 1. Check that correct URL was returned
        assert result_url == "https://res.cloudinary.com/fake_url/avatar.jpg"

        # 2. Check that upload was called with correct parameters
        mock_upload.assert_called_once_with(
            mock_file.file,
            public_id=f"RestApp/{username}",
            overwrite=True,
            resource_type="image",
        )

        # 3. Check that CloudinaryImage was called correctly
        mock_image_class.assert_called_once_with(f"RestApp/{username}")
        mock_image_instance.build_url.assert_called_once_with(
            width=250, height=250, crop="fill", version="1234567890"
        )


def test_upload_file_exception():
    """Test catching Cloudinary error and raising HTTPException (lines 42-47)"""
    mock_file = MagicMock()
    username = "testuser"

    with patch("src.services.upload_file.cloudinary.uploader.upload") as mock_upload:
        # Simulate Cloudinary failure
        mock_upload.side_effect = Exception("Cloudinary connection timeout")

        # Check that our service catches Exception and raises HTTPException 500
        with pytest.raises(HTTPException) as exc_info:
            UploadFileService.upload_file(mock_file, username)

        assert exc_info.value.status_code == 500
        assert "Failed to upload avatar" in exc_info.value.detail
