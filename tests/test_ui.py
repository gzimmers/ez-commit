"""
Tests for the UI components
"""

import pytest
from unittest.mock import patch, call
from ez_commit.ui import TerminalUI

@pytest.fixture
def ui():
    return TerminalUI()

def test_clear_screen(ui):
    with patch('click.echo') as mock_echo:
        ui.clear_screen()
        mock_echo.assert_called_once_with('\033[2J\033[H', nl=False)

def test_clear_lines(ui):
    with patch('click.echo') as mock_echo:
        ui.clear_lines(2)
        assert mock_echo.call_count == 2
        mock_echo.assert_has_calls([
            call('\033[A\033[K', nl=False),
            call('\033[A\033[K', nl=False)
        ])

def test_display_message_basic(ui):
    with patch('click.echo') as mock_echo:
        ui.display_message("Test message")
        assert mock_echo.call_count == 4  # separator, message, separator
        mock_echo.assert_has_calls([
            call("-" * 50),
            call("Test message"),
            call("-" * 50)
        ])

def test_display_message_empty(ui):
    with patch('click.echo') as mock_echo:
        ui.display_message("")
        assert mock_echo.call_count == 4  # Should still show separators
        mock_echo.assert_has_calls([
            call("-" * 50),
            call(""),
            call("-" * 50)
        ])

def test_display_message_whitespace(ui):
    with patch('click.echo') as mock_echo:
        ui.display_message("   \n   ")
        assert mock_echo.call_count == 4
        mock_echo.assert_has_calls([
            call("-" * 50),
            call("   \n   "),
            call("-" * 50)
        ])

def test_display_message_with_title_and_status(ui):
    with patch('click.echo') as mock_echo, \
         patch('click.secho') as mock_secho:
        ui.display_message("Test message", "Title", "Status")
        mock_secho.assert_called_once_with("Status", fg="blue")
        assert "Title" in [call[0][0] for call in mock_echo.call_args_list]

def test_display_message_with_empty_title_and_status(ui):
    with patch('click.echo') as mock_echo, \
         patch('click.secho') as mock_secho:
        ui.display_message("Test message", "", "")
        mock_secho.assert_not_called()
        assert mock_echo.call_count == 4  # Just message and separators

def test_display_actions(ui):
    with patch('click.echo') as mock_echo, \
         patch('click.style') as mock_style:
        ui.display_actions()
        assert mock_echo.call_count == 5  # header + 4 actions
        mock_style.assert_has_calls([
            call("(e)dit", fg="green"),
            call("(c)ancel", fg="red"),
            call("(i)nteractive", fg="yellow"),
            call("(s)ave", fg="blue")
        ])

def test_get_user_choice_valid(ui):
    with patch('click.getchar', return_value='e'), \
         patch('click.echo'):
        choice = ui.get_user_choice()
        assert choice == 'e'

def test_get_user_choice_invalid_then_valid(ui):
    with patch('click.getchar', side_effect=['x', 'e']), \
         patch('click.echo'):
        choice = ui.get_user_choice()
        assert choice == 'e'

def test_get_user_choice_multiple_invalid(ui):
    with patch('click.getchar', side_effect=['x', 'y', 'z', 'e']), \
         patch('click.echo'):
        choice = ui.get_user_choice()
        assert choice == 'e'

def test_get_user_choice_case_insensitive(ui):
    with patch('click.getchar', return_value='E'), \
         patch('click.echo'):
        choice = ui.get_user_choice()
        assert choice == 'e'

def test_get_user_feedback_empty(ui):
    with patch('click.prompt', return_value=""), \
         patch('click.echo'), \
         patch('click.secho'):
        feedback = ui.get_user_feedback("Current message")
        assert feedback == ""

def test_get_user_feedback_whitespace(ui):
    with patch('click.prompt', return_value="   \n   "), \
         patch('click.echo'), \
         patch('click.secho'):
        feedback = ui.get_user_feedback("Current message")
        assert feedback == "   \n   "

def test_get_user_feedback(ui):
    test_message = "Current message"
    expected_feedback = "Test feedback"
    
    with patch('click.prompt', return_value=expected_feedback), \
         patch('click.echo'), \
         patch('click.secho'):
        feedback = ui.get_user_feedback(test_message)
        assert feedback == expected_feedback

def test_confirm_action_yes(ui):
    with patch('click.confirm', return_value=True):
        result = ui.confirm_action("Test confirmation")
        assert result is True

def test_confirm_action_no(ui):
    with patch('click.confirm', return_value=False):
        result = ui.confirm_action("Test confirmation")
        assert result is False

def test_confirm_action_empty_message(ui):
    with patch('click.confirm', return_value=True):
        result = ui.confirm_action("")
        assert result is True

def test_print_error(ui):
    with patch('click.secho') as mock_secho:
        ui._print_error("test error")
        mock_secho.assert_called_once_with(
            "ez-commit: error: test error",
            fg="red",
            err=True
        )

def test_print_error_empty(ui):
    with patch('click.secho') as mock_secho:
        ui._print_error("")
        mock_secho.assert_called_once_with(
            "ez-commit: error: ",
            fg="red",
            err=True
        )

def test_sanitize_error_removes_prefixes(ui):
    test_cases = [
        ("ValueError: test error", "test error"),
        ("Exception: test error", "test error"),
        ("Error: test error", "test error"),
        ("Failed to do something", "do something"),
        ("Unable to do something", "do something"),
    ]
    
    for input_msg, expected in test_cases:
        assert ui._sanitize_error(input_msg) == expected

def test_sanitize_error_handles_none(ui):
    assert ui._sanitize_error(None) == ""

def test_display_error(ui):
    with patch('click.secho') as mock_secho:
        ui.display_error("test error")
        mock_secho.assert_called_once_with(
            "ez-commit: error: test error",
            fg="red",
            err=True
        )

def test_display_error_with_prefix_removal(ui):
    with patch('click.secho') as mock_secho:
        ui.display_error("ValueError: test error")
        mock_secho.assert_called_once_with(
            "ez-commit: error: test error",
            fg="red",
            err=True
        )

def test_display_error_empty(ui):
    with patch('click.secho') as mock_secho:
        ui.display_error("")
        mock_secho.assert_called_once_with(
            "ez-commit: error: ",
            fg="red",
            err=True
        )

def test_display_success(ui):
    with patch('click.secho') as mock_secho:
        ui.display_success("Test success")
        mock_secho.assert_called_once_with(
            "Test success",
            fg="green"
        )

def test_display_info(ui):
    with patch('click.secho') as mock_secho:
        ui.display_info("Test info")
        mock_secho.assert_called_once_with(
            "Test info",
            fg="blue"
        )

def test_display_warning(ui):
    with patch('click.secho') as mock_secho:
        ui.display_warning("Test warning")
        mock_secho.assert_called_once_with(
            "ez-commit: warning: Test warning",
            fg="yellow",
            err=True
        )

def test_display_config_complete(ui):
    test_config = {
        'openai': {
            'model': 'test-model',
            'temperature': 0.7
        },
        'system_prompt': 'test prompt'
    }
    
    with patch('click.echo') as mock_echo, \
         patch('click.secho') as mock_secho, \
         patch('click.style') as mock_style:
        ui.display_config(test_config)
        mock_secho.assert_called_once_with("\nCurrent Configuration:", fg="blue")
        mock_style.assert_has_calls([
            call('test-model', fg='green'),
            call('0.7', fg='green')
        ])
        assert mock_echo.call_count >= 6  # Config has multiple lines

def test_display_config_missing_values(ui):
    test_config = {
        'openai': {
            'model': '',
            'temperature': None
        },
        'system_prompt': ''
    }
    
    with patch('click.echo') as mock_echo, \
         patch('click.secho') as mock_secho, \
         patch('click.style') as mock_style:
        ui.display_config(test_config)
        mock_secho.assert_called_once_with("\nCurrent Configuration:", fg="blue")
        mock_style.assert_has_calls([
            call('', fg='green'),
            call('None', fg='green')
        ])

def test_display_config_missing_sections(ui):
    test_config = {}
    
    with patch('click.echo') as mock_echo, \
         patch('click.secho') as mock_secho:
        ui.display_config(test_config)
        mock_secho.assert_called_once_with("\nCurrent Configuration:", fg="blue")
        # Should handle missing sections gracefully
        assert mock_echo.call_count >= 2  # At least separators should be shown

def test_display_config_invalid_types(ui):
    test_config = {
        'openai': {
            'model': 123,  # Should be string
            'temperature': "0.7"  # Should be float
        },
        'system_prompt': True  # Should be string
    }
    
    with patch('click.echo') as mock_echo, \
         patch('click.secho') as mock_secho, \
         patch('click.style') as mock_style:
        ui.display_config(test_config)
        mock_secho.assert_called_once_with("\nCurrent Configuration:", fg="blue")
        mock_style.assert_has_calls([
            call('123', fg='green'),
            call('0.7', fg='green')
        ])
