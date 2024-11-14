"""
Tests for the command-line interface
"""

import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from ez_commit.cli import main, config, handle_error, create_handlers
from ez_commit.cli import (
    EXIT_SUCCESS,
    EXIT_CANCELLED,
    EXIT_GIT_ERROR,
    EXIT_API_ERROR,
    EXIT_CONFIG_ERROR,
    EXIT_UNKNOWN_ERROR
)

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_handlers():
    ui = Mock()
    commit_handler = Mock()
    config_handler = Mock()
    return ui, commit_handler, config_handler

def test_handle_error():
    ui = Mock()
    error_code = handle_error("test error", EXIT_GIT_ERROR, ui)
    assert error_code == EXIT_GIT_ERROR
    ui.display_error.assert_called_once_with("test error")

def test_create_handlers():
    ui, commit_handler, config_handler = create_handlers()
    assert ui is not None
    assert commit_handler is not None
    assert config_handler is not None

def test_main_preview(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.return_value = (True, None)
        commit_handler.current_message = "test message"
        
        result = runner.invoke(main, ['--preview'])
        
        assert result.exit_code == EXIT_SUCCESS
        ui.display_message.assert_called_once()

def test_main_git_error(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.return_value = (False, "git error")
        
        result = runner.invoke(main)
        
        assert result.exit_code == EXIT_GIT_ERROR
        ui.display_error.assert_called_once()

def test_main_binary_file_error(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.return_value = (False, "Binary files detected in diff")
        
        result = runner.invoke(main)
        
        assert result.exit_code == EXIT_GIT_ERROR
        ui.display_error.assert_called_once()

def test_main_api_error(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.return_value = (False, "OpenAI API error")
        
        result = runner.invoke(main)
        
        assert result.exit_code == EXIT_API_ERROR
        ui.display_error.assert_called_once()

def test_main_invalid_commit_message(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.return_value = (False, "Generated commit message is invalid")
        
        result = runner.invoke(main)
        
        assert result.exit_code == EXIT_UNKNOWN_ERROR
        ui.display_error.assert_called_once()

def test_main_cancel(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.return_value = (True, None)
        commit_handler.current_message = "test message"
        ui.get_user_choice.return_value = 'c'
        
        result = runner.invoke(main)
        
        assert result.exit_code == EXIT_CANCELLED
        ui.display_info.assert_called_with("\nCommit cancelled.")

def test_main_edit(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.return_value = (True, None)
        commit_handler.current_message = "test message"
        ui.get_user_choice.side_effect = ['e', 's']
        commit_handler.handle_save.return_value = (True, None)
        
        result = runner.invoke(main)
        
        assert result.exit_code == EXIT_SUCCESS
        commit_handler.handle_edit.assert_called_once()

def test_main_edit_invalid_message(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.return_value = (True, None)
        commit_handler.current_message = "test message"
        ui.get_user_choice.side_effect = ['e']
        commit_handler.handle_edit.side_effect = ValueError("Invalid commit message format")
        
        result = runner.invoke(main)
        
        assert result.exit_code == EXIT_UNKNOWN_ERROR
        ui.display_error.assert_called_once()

def test_main_interactive(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.return_value = (True, None)
        commit_handler.current_message = "test message"
        ui.get_user_choice.side_effect = ['i', 's']
        commit_handler.handle_interactive.return_value = (True, None)
        commit_handler.handle_save.return_value = (True, None)
        
        result = runner.invoke(main)
        
        assert result.exit_code == EXIT_SUCCESS
        commit_handler.handle_interactive.assert_called_once()

def test_main_interactive_invalid_message(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.return_value = (True, None)
        commit_handler.current_message = "test message"
        ui.get_user_choice.side_effect = ['i']
        commit_handler.handle_interactive.return_value = (False, "Generated commit message is invalid")
        
        result = runner.invoke(main)
        
        assert result.exit_code == EXIT_UNKNOWN_ERROR
        ui.display_error.assert_called_once()

def test_main_save_success(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.return_value = (True, None)
        commit_handler.current_message = "test message"
        ui.get_user_choice.return_value = 's'
        commit_handler.handle_save.return_value = (True, None)
        
        result = runner.invoke(main)
        
        assert result.exit_code == EXIT_SUCCESS
        commit_handler.handle_save.assert_called_once()

def test_main_save_failure(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.return_value = (True, None)
        commit_handler.current_message = "test message"
        ui.get_user_choice.return_value = 's'
        commit_handler.handle_save.return_value = (False, "git error")
        
        result = runner.invoke(main)
        
        assert result.exit_code == EXIT_GIT_ERROR
        ui.display_error.assert_called_once()

# Config command tests
def test_config_edit(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.edit_config.return_value = (True, None)
        
        result = runner.invoke(config, ['edit'])
        
        assert result.exit_code == EXIT_SUCCESS
        config_handler.edit_config.assert_called_once()

def test_config_reset_success(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.reset_config.return_value = (True, None)
        
        result = runner.invoke(config, ['reset'])
        
        assert result.exit_code == EXIT_SUCCESS
        config_handler.reset_config.assert_called_once_with(ui)

def test_config_reset_failure(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.reset_config.return_value = (False, "test error")
        
        result = runner.invoke(config, ['reset'])
        
        assert result.exit_code == EXIT_CONFIG_ERROR
        ui.display_error.assert_called_once()

def test_config_set_api_key_empty(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.set_api_key.return_value = (False, "API key cannot be empty")
        
        result = runner.invoke(config, ['set-api-key', ''])
        
        assert result.exit_code == EXIT_CONFIG_ERROR
        ui.display_error.assert_called_once()

def test_config_set_model_empty(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.set_model.return_value = (False, "Model name cannot be empty")
        
        result = runner.invoke(config, ['set-model', ''])
        
        assert result.exit_code == EXIT_CONFIG_ERROR
        ui.display_error.assert_called_once()

def test_config_set_temperature_invalid(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.set_temperature.return_value = (False, "Temperature must be between 0.0 and 1.0")
        
        result = runner.invoke(config, ['set-temperature', '1.5'])
        
        assert result.exit_code == EXIT_CONFIG_ERROR
        ui.display_error.assert_called_once()

def test_config_set_temperature_scientific(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.set_temperature.return_value = (False, "Temperature must be a decimal number between 0.0 and 1.0")
        
        result = runner.invoke(config, ['set-temperature', '1e-2'])
        
        assert result.exit_code == EXIT_CONFIG_ERROR
        ui.display_error.assert_called_once()

def test_config_edit_prompt_empty(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.edit_prompt.return_value = (False, "System prompt cannot be empty")
        
        result = runner.invoke(config, ['edit-prompt'])
        
        assert result.exit_code == EXIT_CONFIG_ERROR
        ui.display_error.assert_called_once()

def test_config_show_success(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.show_config.return_value = ({}, None)
        
        result = runner.invoke(config, ['show'])
        
        assert result.exit_code == EXIT_SUCCESS
        config_handler.show_config.assert_called_once()

def test_config_show_failure(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.show_config.return_value = ({}, "Failed to load config")
        
        result = runner.invoke(config, ['show'])
        
        assert result.exit_code == EXIT_CONFIG_ERROR
        ui.display_error.assert_called_once()
