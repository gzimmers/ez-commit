# ez-commit

A Python tool that generates commit messages from git diffs using OpenAI's API.

## Installation

```bash
pip install ez-commit
```

## Configuration

Before using ez-commit, you need to set up your OpenAI API key and customize settings as desired. The configuration file will be automatically created at first run in your user config directory.

### Quick Configuration

Set specific configuration values directly from the command line:

```bash
# Set your OpenAI API key
ez-commit config set-api-key your-api-key-here

# Change the OpenAI model
ez-commit config set-model gpt-4

# Adjust temperature (0.0 to 1.0)
ez-commit config set-temperature 0.7

# Edit system prompt in your default editor
ez-commit config edit-prompt

# View current configuration (excluding API key)
ez-commit config show

# Edit the full configuration file
ez-commit config edit
```

### Default Configuration Structure

```yaml
openai:
  api_key: "your-api-key-here"
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 500
system_prompt: |
  You are a helpful assistant that generates clear and concise git commit messages.
  Follow these guidelines:
  - Use the imperative mood ("Add feature" not "Added feature")
  - Keep the first line under 50 characters
  - Provide more detailed explanation in subsequent paragraphs if necessary
  - Reference relevant issue numbers if applicable
  - Focus on the "what" and "why" of the changes, not the "how"
```

## Usage

Simply run `ez-commit` in your git repository:

```bash
# Generate and commit with confirmation
ez-commit

# Preview the generated message without committing
ez-commit --preview
```

### Configuration Commands

```bash
# Show all configuration commands
ez-commit config --help

# Show current configuration
ez-commit config show

# Edit system prompt
ez-commit config edit-prompt

# Set OpenAI model
ez-commit config set-model gpt-4

# Set temperature
ez-commit config set-temperature 0.7
```

## How It Works

1. When you run `ez-commit`, it:
   - Gets the current git diff (staged changes, or unstaged if nothing is staged)
   - Sends the diff to OpenAI's API with your configured system prompt
   - Generates an appropriate commit message
   - Shows you the message for confirmation
   - If you confirm, stages all changes (if needed) and commits them

2. The system prompt can be customized to generate commit messages that match your preferred style and format.

## Environment Variables

- `OPENAI_API_KEY`: Can be used instead of setting the API key in the config file
- `EDITOR`: Used when editing the system prompt or configuration file

## License

MIT License
