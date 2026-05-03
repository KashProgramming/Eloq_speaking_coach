import pytest
from app.services.storage_service import extract_public_id_from_url, delete_audio, delete_multiple_audios


class TestExtractPublicId:
    """Test public_id extraction from Cloudinary URLs"""
    
    def test_standard_url(self):
        url = "https://res.cloudinary.com/demo/video/upload/v1234567890/eloq_audio/test_file.mp3"
        result = extract_public_id_from_url(url)
        assert result == "eloq_audio/test_file"
    
    def test_url_without_version(self):
        url = "https://res.cloudinary.com/demo/video/upload/eloq_audio/test_file.mp3"
        result = extract_public_id_from_url(url)
        assert result == "eloq_audio/test_file"
    
    def test_url_with_nested_folder(self):
        url = "https://res.cloudinary.com/demo/video/upload/v1234567890/folder1/folder2/file.mp3"
        result = extract_public_id_from_url(url)
        assert result == "folder1/folder2/file"
    
    def test_empty_url(self):
        result = extract_public_id_from_url("")
        assert result is None
    
    def test_none_url(self):
        result = extract_public_id_from_url(None)
        assert result is None
    
    def test_invalid_url(self):
        url = "https://example.com/some/path/file.mp3"
        result = extract_public_id_from_url(url)
        assert result is None


class TestDeleteMultipleAudios:
    """Test batch audio deletion"""
    
    def test_empty_list(self):
        result = delete_multiple_audios([])
        assert result["success"] == 0
        assert result["failed"] == 0
        assert result["skipped"] == 0
    
    def test_list_with_none_values(self):
        result = delete_multiple_audios([None, "", None])
        assert result["skipped"] == 3
        assert result["success"] == 0
        assert result["failed"] == 0


# Note: Actual Cloudinary deletion tests would require mocking or a test environment
# These tests verify the logic without making real API calls
