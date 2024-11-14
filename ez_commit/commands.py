"""
Command handlers for ez-commit
"""

import os
import subprocess
import tempfile
from typing import Optional, Tuple

class EditorHandler:
    """Handles editor-related operations."""
    
    def __init__(self):
        self.editor = os.environ.get('EDITOR', 'vim')

    def open_editor(self, filename: str) -> None:
        """Open the editor with the given file."""
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['notepad', filename], check=True)
            else:
                subprocess.run([self.editor, filename], check=True)
        except subprocess.SubprocessError as e:
            raise ValueError(f"Failed to open editor: {str(e)}")

    def edit_text(self, initial_text: str = "") -> str:
        """Edit text in a temporary file."""
        try:
            # Use UTF-8 encoding explicitly
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False, encoding='utf-8') as tf:
                tf.write(initial_text)
                tf.flush()
                filename = tf.name
            
            self.open_editor(filename)
            
            # Read with UTF-8 encoding
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            os.unlink(filename)
            return content.strip()
        except (IOError, OSError) as e:
            raise ValueError(f"File operation error: {str(e)}")
        finally:
            # Ensure temp file is cleaned up even if an error occurs
            try:
                if 'filename' in locals():
                    os.unlink(filename)
            except:
                pass

class CommitHandler:
    """Handles commit-related operations."""
    
    def __init__(self, ui, core, editor_handler):
        self.ui = ui
        self.core = core
        self.editor = editor_handler
        self._diff = None
        self._message = None

    def validate_commit_message(self, message: str) -> bool:
        """Validate commit message format."""
        if not message or not message.strip():
            return False
            
        lines = message.splitlines()
        if not lines:
            return False
            
        # First line should be under 50 chars and not empty
        if len(lines[0]) > 50 or not lines[0].strip():
            return False
            
        return True

    def initialize(self) -> Tuple[bool, Optional[str]]:
        """Initialize the commit process."""
        try:
            self._diff = self.core.get_git_diff()
            self._message = self.core.generate_commit_message(self._diff)
            
            if not self.validate_commit_message(self._message):
                return False, "Generated commit message is invalid"
                
            return True, None
        except ValueError as e:
            return False, str(e)

    def handle_edit(self) -> None:
        """Handle edit action."""
        edited_message = self.editor.edit_text(self._message)
        if edited_message and self.validate_commit_message(edited_message):
            self._message = edited_message
        else:
            raise ValueError("Invalid commit message format. First line must be non-empty and under 50 characters.")

    def handle_interactive(self) -> Tuple[bool, Optional[str]]:
        """Handle interactive feedback mode."""
        feedback = self.ui.get_user_feedback(self._message)
        
        if not feedback.strip():
            return True, None
            
        try:
            additional_messages = [
                {"role": "assistant", "content": self._message},
                {"role": "user", "content": f"Suggested changes: {feedback}"}
            ]
            new_message = self.core.generate_commit_message(self._diff, additional_messages)
            
            if not self.validate_commit_message(new_message):
                return False, "Generated commit message is invalid"
                
            self._message = new_message
            return True, None
        except ValueError as e:
            return False, str(e)

    def handle_save(self) -> Tuple[bool, Optional[str]]:
        """Handle save action."""
        try:
            if not self.validate_commit_message(self._message):
                return False, "Invalid commit message format"
                
            self.core.commit_changes(self._message)
            return True, None
        except ValueError as e:
            return False, str(e)

    @property
    def current_message(self) -> str:
        """Get the current commit message."""
        return self._message

class ConfigHandler:
    """Handles configuration operations."""
    
    def __init__(self, config_module, editor_handler):
        self.config = config_module
        self.editor = editor_handler

    def edit_config(self) -> Tuple[bool, Optional[str]]:
        """Edit the configuration file."""
        try:
            self.config.ensure_config_exists()
            config_file = self.config.get_config_file()
            self.editor.open_editor(str(config_file))
            
            # Validate config after edit
            self.config.load_config()
            return True, None
        except Exception as e:
            return False, str(e)

    def reset_config(self, ui) -> Tuple[bool, Optional[str]]:
        """Reset configuration to default values."""
        try:
            self.config.ensure_config_exists()
            
            # Show current config before asking for confirmation
            current_config = self.config.load_config()
            ui.display_config(current_config)
            
            if ui.confirm_action("Are you sure you want to reset to default configuration?"):
                self.config.reset_config()
                ui.display_success("Configuration reset to defaults.")
                
                # Show new config
                new_config = self.config.load_config()
                ui.display_config(new_config)
                return True, None
            else:
                ui.display_info("Reset cancelled.")
                return True, None
        except Exception as e:
            return False, str(e)

    def set_api_key(self, key: str) -> Tuple[bool, Optional[str]]:
        """Set the OpenAI API key."""
        if not key or not key.strip():
            return False, "API key cannot be empty"
            
        try:
            self.config.ensure_config_exists()
            cfg = self.config.load_config()
            cfg["openai"]["api_key"] = key.strip()
            self.config.save_config(cfg)
            return True, None
        except Exception as e:
            return False, str(e)

    def set_model(self, model: str) -> Tuple[bool, Optional[str]]:
        """Set the OpenAI model."""
        if not model or not model.strip():
            return False, "Model name cannot be empty"
            
        try:
            self.config.ensure_config_exists()
            cfg = self.config.load_config()
            cfg["openai"]["model"] = model.strip()
            self.config.save_config(cfg)
            return True, None
        except Exception as e:
            return False, str(e)

    def set_temperature(self, temperature: float) -> Tuple[bool, Optional[str]]:
        """Set the temperature for response generation."""
        try:
            # Convert to float to handle string inputs
            temp = float(temperature)
            
            # Validate range and format
            if not (0 <= temp <= 1):
                return False, "Temperature must be between 0.0 and 1.0"
                
            # Check for scientific notation
            if 'e' in str(temp).lower():
                return False, "Temperature must be a decimal number between 0.0 and 1.0"
            
            self.config.ensure_config_exists()
            cfg = self.config.load_config()
            cfg["openai"]["temperature"] = temp
            self.config.save_config(cfg)
            return True, None
        except ValueError:
            return False, "Temperature must be a valid number between 0.0 and 1.0"
        except Exception as e:
            return False, str(e)

    def edit_prompt(self) -> Tuple[bool, Optional[str]]:
        """Edit the system prompt."""
        try:
            self.config.ensure_config_exists()
            cfg = self.config.load_config()
            current_prompt = cfg["system_prompt"]
            
            new_prompt = self.editor.edit_text(current_prompt)
            if new_prompt and new_prompt.strip():
                cfg["system_prompt"] = new_prompt
                self.config.save_config(cfg)
                return True, None
            return False, "System prompt cannot be empty"
        except Exception as e:
            return False, str(e)

    def show_config(self) -> Tuple[dict, Optional[str]]:
        """Show current configuration."""
        try:
            self.config.ensure_config_exists()
            return self.config.load_config(), None
        except Exception as e:
            return {}, str(e)
