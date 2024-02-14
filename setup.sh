
#!/bin/bash

# Check Python version
PYTHON_VERSION="3.10.10"  # Replace with your desired version

# if ! command -v python3 &> /dev/null; then
#   echo "Python 3 is not installed."
#   exit 1
# elif [[ $(python3 --version | grep -oE "[0-9]+\.[0-9]+\.[0-9]+") != "$PYTHON_VERSION" ]]; then
#   echo "Python version $PYTHON_VERSION is required."
#   exit 1
# fi

# Get virtual environment name (optional: allow passing as argument)
VENV_NAME="venv"

# Create virtual environment
if ! virtualenv -p python3 "$VENV_NAME"; then
  echo "Failed to create virtual environment '$VENV_NAME'."
  exit 1
fi

# Activate virtual environment
source "$VENV_NAME/bin/activate"

# Install dependencies (allow different requirements.txt locations)
REQUIREMENTS_FILE="./requirements.txt"  # Change path if needed
if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
  echo "Requirements file '$REQUIREMENTS_FILE' not found."
  exit 1
fi

if ! pip install -r "$REQUIREMENTS_FILE"; then
  echo "Failed to install dependencies from '$REQUIREMENTS_FILE'."
  exit 1
fi

echo "Development environment setup complete."

# Exit with success code
exit 0