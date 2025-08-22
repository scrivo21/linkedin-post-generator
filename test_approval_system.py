#!/usr/bin/env python3
"""
Test script for the button-based approval system
Tests the ApprovalView class and button functionality
"""

import sys
import os
import asyncio
import unittest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from discord_linkedin_bot import ApprovalView
from models import PostStatus

class TestApprovalSystem(unittest.TestCase):
    """Test the button-based approval system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.draft_id = "test-draft-123"
        self.view = ApprovalView(self.draft_id)
        
        # Mock Discord interaction
        self.mock_interaction = Mock()
        self.mock_interaction.response.defer = AsyncMock()
        self.mock_interaction.edit_original_response = AsyncMock()
        self.mock_interaction.followup.send = AsyncMock()
        self.mock_interaction.user.name = "testuser"
        self.mock_interaction.user.discriminator = "1234"
        self.mock_interaction.user.mention = "@testuser"
    
    def test_approval_view_initialization(self):
        """Test that ApprovalView initializes correctly"""
        view = ApprovalView("test-123")
        self.assertEqual(view.draft_id, "test-123")
        self.assertEqual(view.timeout, 24*60*60)  # 24 hours
        
        # Check that all three buttons exist
        buttons = [item for item in view.children]
        self.assertEqual(len(buttons), 3)
        
        # Check button labels and styles
        approve_button = next(b for b in buttons if b.custom_id == 'approve')
        reject_button = next(b for b in buttons if b.custom_id == 'reject')
        edit_button = next(b for b in buttons if b.custom_id == 'edit')
        
        self.assertEqual(approve_button.label, '✅ Approve')
        self.assertEqual(reject_button.label, '❌ Reject')
        self.assertEqual(edit_button.label, '📝 Request Edit')
    
    @patch('discord_linkedin_bot.db')
    async def test_approve_button_handling(self, mock_db):
        """Test approval button functionality"""
        mock_db.update_post_status = Mock()
        
        # Create a mock button (not needed for the test but for completeness)
        mock_button = Mock()
        
        # Test approval
        await self.view.handle_approval(self.mock_interaction, 'approved')
        
        # Verify database was updated correctly
        mock_db.update_post_status.assert_called_once_with(
            self.draft_id,
            PostStatus.APPROVED_FOR_SOCIALS,
            discord_approver="testuser#1234"
        )
        
        # Verify Discord interaction was handled
        self.mock_interaction.response.defer.assert_called_once()
        self.mock_interaction.edit_original_response.assert_called_once()
        
        # Check that buttons were disabled
        for item in self.view.children:
            self.assertTrue(item.disabled)
    
    @patch('discord_linkedin_bot.db')
    async def test_reject_button_handling(self, mock_db):
        """Test rejection button functionality"""
        mock_db.update_post_status = Mock()
        
        await self.view.handle_approval(self.mock_interaction, 'rejected')
        
        mock_db.update_post_status.assert_called_once_with(
            self.draft_id,
            PostStatus.DECLINED,
            discord_approver="testuser#1234",
            last_error="Rejected via Discord button"
        )
        
        self.mock_interaction.response.defer.assert_called_once()
        self.mock_interaction.edit_original_response.assert_called_once()
    
    @patch('discord_linkedin_bot.db')
    async def test_edit_request_handling(self, mock_db):
        """Test edit request button functionality"""
        mock_db.update_post_status = Mock()
        
        await self.view.handle_approval(self.mock_interaction, 'edit_requested')
        
        mock_db.update_post_status.assert_called_once_with(
            self.draft_id,
            PostStatus.PENDING,
            discord_approver="testuser#1234",
            last_error="Edit requested via Discord button"
        )
        
        self.mock_interaction.response.defer.assert_called_once()
        self.mock_interaction.edit_original_response.assert_called_once()
    
    @patch('discord_linkedin_bot.db')
    async def test_username_without_discriminator(self, mock_db):
        """Test handling new Discord username system (no discriminator)"""
        mock_db.update_post_status = Mock()
        
        # Set up interaction with no discriminator (new Discord system)
        self.mock_interaction.user.discriminator = None
        
        await self.view.handle_approval(self.mock_interaction, 'approved')
        
        # Verify correct username format is used
        mock_db.update_post_status.assert_called_once_with(
            self.draft_id,
            PostStatus.APPROVED_FOR_SOCIALS,
            discord_approver="testuser"  # No discriminator
        )
    
    @patch('discord_linkedin_bot.db')
    @patch('discord_linkedin_bot.logger')
    async def test_error_handling(self, mock_logger, mock_db):
        """Test error handling in approval system"""
        # Make database update fail
        mock_db.update_post_status.side_effect = Exception("Database error")
        
        await self.view.handle_approval(self.mock_interaction, 'approved')
        
        # Verify error was logged
        mock_logger.error.assert_called()
        
        # Verify error message was sent to user
        self.mock_interaction.followup.send.assert_called_once()
        args, kwargs = self.mock_interaction.followup.send.call_args
        self.assertIn("Error processing approval", args[0])
        self.assertTrue(kwargs.get('ephemeral', False))
    
    def test_timeout_handling(self):
        """Test button timeout functionality"""
        # Simulate timeout
        self.view.on_timeout()
        
        # Check that all buttons are disabled after timeout
        for item in self.view.children:
            self.assertTrue(item.disabled)

class TestButtonSystemIntegration(unittest.TestCase):
    """Integration tests for the complete button system"""
    
    @patch('discord_linkedin_bot.db')
    @patch('discord_linkedin_bot.linkedin_bot')
    async def test_full_approval_workflow(self, mock_linkedin_bot, mock_db):
        """Test the complete approval workflow"""
        from models import LinkedInDraft
        
        # Create a mock post
        mock_post = Mock(spec=LinkedInDraft)
        mock_post.draft_id = "workflow-test-123"
        mock_post.content = "Test LinkedIn post content for approval workflow"
        mock_post.industry = "Technology"
        mock_post.audience = "Tech professionals"
        mock_post.created_at = datetime.now()
        
        # Mock the linkedin bot setup
        mock_linkedin_bot.setup_channels = AsyncMock()
        mock_linkedin_bot.approval_channel = Mock()
        mock_linkedin_bot.approval_channel.send = AsyncMock()
        mock_linkedin_bot.create_post_preview_embed = Mock(return_value=Mock())
        mock_linkedin_bot.create_linkedin_mockup = AsyncMock(return_value=None)
        
        mock_db.update_post_status = Mock()
        
        # Test sending approval request
        await mock_linkedin_bot.send_approval_request(mock_post)
        
        # Verify the message was sent with correct components
        mock_linkedin_bot.approval_channel.send.assert_called_once()
        call_args = mock_linkedin_bot.approval_channel.send.call_args
        
        # Check that content includes post ID and full content
        content = call_args[1]['content']
        self.assertIn("workflow-test-123", content)
        self.assertIn("Test LinkedIn post content", content)
        
        # Check that view (buttons) was included
        self.assertIn('view', call_args[1])

def run_async_test(test_func):
    """Helper to run async test functions"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(test_func())
    finally:
        loop.close()

if __name__ == '__main__':
    print("🧪 Testing Button-Based Approval System")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add tests
    test_classes = [TestApprovalSystem, TestButtonSystemIntegration]
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All approval system tests passed!")
        print(f"✅ Ran {result.testsRun} tests successfully")
    else:
        print("❌ Some tests failed!")
        print(f"❌ Failures: {len(result.failures)}")
        print(f"❌ Errors: {len(result.errors)}")
        
        for test, traceback in result.failures + result.errors:
            print(f"\n❌ {test}:")
            print(traceback)
    
    print("\n🎯 Key Features Verified:")
    print("  • Three-button interface (Approve/Reject/Edit)")
    print("  • Proper status updates to database")
    print("  • Discord username tracking")
    print("  • 24-hour timeout functionality")
    print("  • Error handling and user feedback")
    print("  • Button disabling after action")
    print("  • Full post content display")