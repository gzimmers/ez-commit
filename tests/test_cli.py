"""
Tests for the command-line interface
"""

import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from ez_commit.cli import main, config, create_handlers
from ez_commit.exceptions import GitError, APIError, ConfigError, EditorError

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_handlers():
    ui = Mock()
    commit_handler = Mock()
    config_handler = Mock()
    return ui, commit_handler, config_handler

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
        
        assert result.exit_code == 0
        ui.display_message.assert_called_once()

def test_main_git_error(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.side_effect = GitError("could not read git diff")
        
        result = runner.invoke(main)
        
        assert result.exit_code == 2
        ui.display_error.assert_called_once_with("could not read git diff")

def test_main_binary_file_error(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.side_effect = GitError("binary files detected in diff")
        
        result = runner.invoke(main)
        
        assert result.exit_code == 2
        ui.display_error.assert_called_once_with("binary files detected in diff")

def test_main_api_error(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.side_effect = APIError("could not connect to OpenAI API")
        
        result = runner.invoke(main)
        
        assert result.exit_code == 3
        ui.display_error.assert_called_once_with("could not connect to OpenAI API")

def test_main_invalid_commit_message(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.side_effect = GitError("invalid commit message format")
        
        result = runner.invoke(main)
        
        assert result.exit_code == 2
        ui.display_error.assert_called_once_with("invalid commit message format")

def test_main_cancel(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.return_value = (True, None)
        commit_handler.current_message = "test message"
        ui.get_user_choice.return_value = 'c'
        
        result = runner.invoke(main)
        
        assert result.exit_code == 1
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
        
        assert result.exit_code == 0
        commit_handler.handle_edit.assert_called_once()

def test_main_edit_invalid_message(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.return_value = (True, None)
        commit_handler.current_message = "test message"
        ui.get_user_choice.side_effect = ['e']
        commit_handler.handle_edit.side_effect = GitError("first line must be non-empty and under 50 characters")
        
        result = runner.invoke(main)
        
        assert result.exit_code == 2
        ui.display_error.assert_called_once_with("first line must be non-empty and under 50 characters")

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
        
        assert result.exit_code == 0
        commit_handler.handle_interactive.assert_called_once()

def test_main_interactive_api_error(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.return_value = (True, None)
        commit_handler.current_message = "test message"
        ui.get_user_choice.side_effect = ['i']
        commit_handler.handle_interactive.side_effect = APIError("could not generate new commit message")
        
        result = runner.invoke(main)
        
        assert result.exit_code == 3
        ui.display_error.assert_called_once_with("could not generate new commit message")

def test_main_save_success(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.return_value = (True, None)
        commit_handler.current_message = "test message"
        ui.get_user_choice.return_value = 's'
        commit_handler.handle_save.return_value = (True, None)
        
        result = runner.invoke(main)
        
        assert result.exit_code == 0
        commit_handler.handle_save.assert_called_once()

def test_main_save_failure(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, commit_handler, _ = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, commit_handler, None)
        commit_handler.initialize.return_value = (True, None)
        commit_handler.current_message = "test message"
        ui.get_user_choice.return_value = 's'
        commit_handler.handle_save.side_effect = GitError("could not commit changes")
        
        result = runner.invoke(main)
        
        assert result.exit_code == 2
        ui.display_error.assert_called_once_with("could not commit changes")

# Config command tests
def test_config_edit(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.edit_config.return_value = (True, None)
        
        result = runner.invoke(config, ['edit'])
        
        assert result.exit_code == 0
        config_handler.edit_config.assert_called_once()

def test_config_reset_success(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.reset_config.return_value = (True, None)
        
        result = runner.invoke(config, ['reset'])
        
        assert result.exit_code == 0
        config_handler.reset_config.assert_called_once_with(ui)

def test_config_reset_failure(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.reset_config.side_effect = ConfigError("could not reset configuration")
        
        result = runner.invoke(config, ['reset'])
        
        assert result.exit_code == 4
        ui.display_error.assert_called_once_with("could not reset configuration")

def test_config_set_api_key_empty(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.set_api_key.return_value = (False, "API key cannot be empty")
        
        result = runner.invoke(config, ['set-api-key', ''])
        
        assert result.exit_code == 4
        ui.display_error.assert_called_once_with("API key cannot be empty")

def test_config_set_model_empty(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.set_model.return_value = (False, "model name cannot be empty")
        
        result = runner.invoke(config, ['set-model', ''])
        
        assert result.exit_code == 4
        ui.display_error.assert_called_once_with("model name cannot be empty")

def test_config_set_temperature_invalid(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.set_temperature.return_value = (False, "temperature must be between 0.0 and 1.0")
        
        result = runner.invoke(config, ['set-temperature', '1.5'])
        
        assert result.exit_code == 4
        ui.display_error.assert_called_once_with("temperature must be between 0.0 and 1.0")

def test_config_set_temperature_scientific(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.set_temperature.return_value = (False, "temperature must be a decimal number between 0.0 and 1.0")
        
        result = runner.invoke(config, ['set-temperature', '1e-2'])
        
        assert result.exit_code == 4
        ui.display_error.assert_called_once_with("temperature must be a decimal number between 0.0 and 1.0")

def test_config_edit_prompt_empty(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.edit_prompt.return_value = (False, "system prompt cannot be empty")
        
        result = runner.invoke(config, ['edit-prompt'])
        
        assert result.exit_code == 4
        ui.display_error.assert_called_once_with("system prompt cannot be empty")

def test_config_show_success(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.show_config.return_value = ({}, None)
        
        result = runner.invoke(config, ['show'])
        
        assert result.exit_code == 0
        config_handler.show_config.assert_called_once()

def test_config_show_failure(runner):
    with patch('ez_commit.cli.create_handlers') as mock_create:
        ui, _, config_handler = Mock(), Mock(), Mock()
        mock_create.return_value = (ui, None, config_handler)
        config_handler.show_config.side_effect = ConfigError("could not load configuration")
        
        result = runner.invoke(config, ['show'])
        
        assert result.exit_code == 4
        ui.display_error.assert_called_once_with("could not load configuration")
