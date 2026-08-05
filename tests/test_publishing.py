"""Tests for Publishing Adapters (Phase 11)."""

from unittest.mock import Mock, patch

import pytest
from hermes_social.config import AppConfig
from hermes_social.constants import Platform
from hermes_social.publishing.manual import ManualApprovalPublisher
from hermes_social.publishing.registry import get_publisher, validate_all_publishers
from hermes_social.publishing.linkedin import LinkedInPublisher
from hermes_social.publishing.models import PublishPayload


@pytest.fixture
def mock_config():
    config = AppConfig()
    config.publishing_enabled = True
    config.publishing_dry_run = False
    return config


def test_registry_fallback(mock_config):
    # Missing credentials for all platforms, so they should fallback to Manual
    publisher = get_publisher(Platform.LINKEDIN, mock_config)
    assert isinstance(publisher, ManualApprovalPublisher)


def test_manual_publisher(mock_config):
    publisher = ManualApprovalPublisher(mock_config)
    
    assert publisher.validate_credentials() is True
    
    post = {
        "id": 1,
        "platform": "linkedin",
        "body": "Test post",
        "hashtags": "#test"
    }
    
    payload = publisher.prepare_payload(post, [])
    assert payload.platform == Platform.LINKEDIN
    assert payload.text == "Test post"
    
    result = publisher.publish(payload)
    assert result.success is False
    assert result.fallback_triggered is True


def test_registry_linkedin(mock_config):
    mock_config.linkedin_access_token = "valid_token"
    
    with patch("hermes_social.publishing.linkedin.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        publisher = get_publisher(Platform.LINKEDIN, mock_config)
        assert isinstance(publisher, LinkedInPublisher)


def test_linkedin_prepare_payload(mock_config):
    mock_config.linkedin_access_token = "valid_token"
    publisher = LinkedInPublisher(mock_config)
    
    post = {
        "id": 1,
        "platform": "linkedin",
        "body": "Test body",
        "hashtags": "#AI #Agents"
    }
    
    payload = publisher.prepare_payload(post, [{"path": "/tmp/img.png"}])
    
    assert payload.platform == Platform.LINKEDIN
    assert "Test body" in payload.text
    assert "#AI #Agents" in payload.text
    assert len(payload.media_paths) == 1


def test_validate_all_publishers(mock_config):
    with patch("hermes_social.publishing.linkedin.LinkedInPublisher.validate_credentials", return_value=True), \
         patch("hermes_social.publishing.instagram.InstagramPublisher.validate_credentials", return_value=False), \
         patch("hermes_social.publishing.x_publisher.XPublisher.validate_credentials", return_value=False):
         
        results = validate_all_publishers(mock_config)
        assert results["linkedin"] is True
        assert results["instagram"] is False
        assert results["x"] is False
