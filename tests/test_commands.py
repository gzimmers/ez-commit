"""
Tests for the command handlers
"""

import os
import pytest
from unittest.mock import Mock, patch, mock_open, call
from ez_commit.commands import EditorHandler, CommitHandler, ConfigHandler

# EditorHandler Tests
@pytest.fixture
def editor_handler():
    return EditorHandler()

def test_editor_handler_init():
    with patch.dict(os.environ, {'EDITOR': 'nano'}):
        handler = EditorHandler()
        assert handler.editor == 'nano'

def test_editor_handler_default_editor():
    with patch.dict(os.environ, clear=True):
        handler = EditorHandler()
        assert handler.editor == 'vim'

def test_open_editor_unix(editor_handler):
    with patch('subprocess.run') as mock_run:
        editor_handler.open_editor('test.txt')
        mock_run.assert_called_once_with([editor_handler.editor, 'test.txt'], check=True)

def test_open_editor_windows():
    with patch('os.name', 'nt'), \
         patch('subprocess.run') as mock_run:
        editor_handler = EditorHandler()
        editor_handler.open_editor('test.txt')
        mock_run.assert_called_once_with(['notepad', 'test.txt'], check=True)

def test_open_editor_failure(editor_handler):
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.SubprocessError("test error")
        with pytest.raises(ValueError, match="Failed to open editor"):
            editor_handler.open_editor('test.txt')

def test_edit_text_utf8(editor_handler):
    test_content = "test content 你好"
    mock_file = mock_open(read_data=test_content)
    
    with patch('tempfile.NamedTemporaryFile', mock_open()), \
         patch('builtins.open', mock_file), \
         patch.object(editor_handler, 'open_editor'), \
         patch('os.unlink'):
        result = editor_handler.edit_text("initial text")
        assert result == test_content.strip()
        # Verify UTF-8 encoding was used
        mock_file.assert_has_calls([
            call(mock_file.return_value.name, 'r', encoding='utf-8')
        ])

def test_edit_text_cleanup_on_error(editor_handler):
    with patch('tempfile.NamedTemporaryFile') as mock_temp, \
         patch('os.unlink') as mock_unlink, \
         patch.object(editor_handler, 'open_editor') as mock_editor:
        mock_temp.return_value.__enter__.return_value.name = 'test.txt'
        mock_editor.side_effect = ValueError("test error")
        
        with pytest.raises(ValueError):
            editor_handler.edit_text("test")
        
        mock_unlink.assert_called_once_with('test.txt')

# CommitHandler Tests
@pytest.fixture
def mock_dependencies():
    return {
        'ui': Mock(),
        'core': Mock(),
        'editor': Mock()
    }

@pytest.fixture
def commit_handler(mock_dependencies):
    return CommitHandler(
        mock_dependencies['ui'],
        mock_dependencies['core'],
        mock_dependencies['editor']
    )

def test_validate_commit_message(commit_handler):
    # Valid message
    assert commit_handler.validate_commit_message("Add feature") is True
    
    # Empty message
    assert commit_handler.validate_commit_message("") is False
    assert commit_handler.validate_commit_message("   ") is False
    
    # First line too long
    long_message = "x" * 51
    assert commit_handler.validate_commit_message(long_message) is False
    
    # Empty first line
    assert commit_handler.validate_commit_message("\nSecond line") is False

def test_commit_handler_initialize_success(commit_handler, mock_dependencies):
    mock_dependencies['core'].get_git_diff.return_value = "test diff"
    mock_dependencies['core'].generate_commit_message.return_value = "Add feature"
    
    success, error = commit_handler.initialize()
    
    assert success is True
    assert error is None
    assert commit_handler.current_message == "Add feature"

def test_commit_handler_initialize_invalid_message(commit_handler, mock_dependencies):
    mock_dependencies['core'].get_git_diff.return_value = "test diff"
    mock_dependencies['core'].generate_commit_message.return_value = "x" * 51  # Too long
    
    success, error = commit_handler.initialize()
    
    assert success is False
    assert error == "Generated commit message is invalid"

def test_handle_edit_invalid_message(commit_handler, mock_dependencies):
    commit_handler._message = "original message"
    mock_dependencies['editor'].edit_text.return_value = "x" * 51  # Too long
    
    with pytest.raises(ValueError, match="Invalid commit message format"):
        commit_handler.handle_edit()

def test_handle_interactive_invalid_message(commit_handler, mock_dependencies):
    commit_handler._message = "original message"
    commit_handler._diff = "test diff"
    mock_dependencies['ui'].get_user_feedback.return_value = "test feedback"
    mock_dependencies['core'].generate_commit_message.return_value = "x" * 51  # Too long
    
    success, error = commit_handler.handle_interactive()
    
    assert success is False
    assert error == "Generated commit message is invalid"

def test_handle_save_invalid_message(commit_handler, mock_dependencies):
    commit_handler._message = "x" * 51  # Too long
    
    success, error = commit_handler.handle_save()
    
    assert success is False
    assert error == "Invalid commit message format"

# ConfigHandler Tests
@pytest.fixture
def config_handler(mock_dependencies):
    return ConfigHandler(Mock(), mock_dependencies['editor'])

def test_set_api_key_empty(config_handler):
    success, error = config_handler.set_api_key("")
    assert success is False
    assert error == "API key cannot be empty"
    
    success, error = config_handler.set_api_key("   ")
    assert success is False
    assert error == "API key cannot be empty"

def test_set_model_empty(config_handler):
    success, error = config_handler.set_model("")
    assert success is False
    assert error == "Model name cannot be empty"
    
    success, error = config_handler.set_model("   ")
    assert success is False
    assert error == "Model name cannot be empty"

def test_set_temperature_scientific_notation(config_handler):
    success, error = config_handler.set_temperature(1e-2)
    assert success is False
    assert error == "Temperature must be a decimal number between 0.0 and 1.0"

def test_set_temperature_string_input(config_handler):
    success, error = config_handler.set_temperature("0.5")
    assert success is True
    assert error is None
    
    success, error = config_handler.set_temperature("invalid")
    assert success is False
    assert error == "Temperature must be a valid number between 0.0 and 1.0"

def test_edit_prompt_empty(config_handler):
    config_handler.config.load_config.return_value = {"system_prompt": "old prompt"}
    config_handler.editor.edit_text.return_value = "   "
    
    success, error = config_handler.edit_prompt()
    assert success is False
    assert error == "System prompt cannot be empty"

def test_edit_config_validation_error(config_handler):
    config_handler.config.load_config.side_effect = ValueError("Invalid config")
    
    success, error = config_handler.edit_config()
    assert success is False
    assert error == "Invalid config"

def test_reset_config_success_confirmed(config_handler):
    ui = Mock()
    ui.confirm_action.return_value = True
    
    success, error = config_handler.reset_config(ui)
    
    assert success is True
    assert error is None
    config_handler.config.reset_config.assert_called_once()
    ui.display_success.assert_called_once_with("Configuration reset to defaults.")

def test_reset_config_cancelled(config_handler):
    ui = Mock()
    ui.confirm_action.return_value = False
    
    success, error = config_handler.reset_config(ui)
    
    assert success is True
    assert error is None
    config_handler.config.reset_config.assert_not_called()
    ui.display_info.assert_called_once_with("Reset cancelled.")

def test_set_api_key_success(config_handler):
    success, error = config_handler.set_api_key("test-key")
    
    assert success is True
    assert error is None
    config_handler.config.load_config.assert_called_once()
    config_handler.config.save_config.assert_called_once()

def test_set_model_success(config_handler):
    success, error = config_handler.set_model("test-model")
    
    assert success is True
    assert error is None
    config_handler.config.load_config.assert_called_once()
    config_handler.config.save_config.assert_called_once()

def test_set_temperature_success(config_handler):
    success, error = config_handler.set_temperature(0.5)
    
    assert success is True
    assert error is None
    config_handler.config.load_config.assert_called_once()
    config_handler.config.save_config.assert_called_once()

def test_set_temperature_invalid(config_handler):
    success, error = config_handler.set_temperature(1.5)
    
    assert success is False
    assert error == "Temperature must be between 0.0 and 1.0"
    config_handler.config.load_config.assert_not_called()
    config_handler.config.save_config.assert_not_called()

def test_edit_prompt_success(config_handler):
    config_handler.config.load_config.return_value = {"system_prompt": "old prompt"}
    config_handler.editor.edit_text.return_value = "new prompt"
    
    success, error = config_handler.edit_prompt()
    
    assert success is True
    assert error is None
    config_handler.config.save_config.assert_called_once()

def test_show_config_success(config_handler):
    test_config = {"test": "config"}
    config_handler.config.load_config.return_value = test_config
    
    config, error = config_handler.show_config()
    
    assert config == test_config
    assert error is None

def test_show_config_failure(config_handler):
    config_handler.config.load_config.side_effect = Exception("test error")
    
    config, error = config_handler.show_config()
    
    assert config == {}
    assert error == "test error"
