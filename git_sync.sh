#!/bin/zsh

# Stop script immediately if any command fails
set -e

# Target directory and commit message configuration
TARGET_DIR="${1:-./my-repo}"
COMMIT_MSG="${2:-Auto-commit: update repository files}"

# -----------------------------------------------------------------------------
# 1. Check if Git is installed, install if missing
# -----------------------------------------------------------------------------
if ! command -v git &> /dev/null; then
  echo "Git is not installed. Attempting installation..."
  
  if [[ "$OSTYPE" == "darwin"* ]]; then
    if command -v brew &> /dev/null; then
      brew install git
    else
      echo "Error: Homebrew not found. Please install Homebrew or Xcode Command Line Tools manually."
      exit 1
    fi
  elif [[ -f /etc/debian_version ]]; then
    sudo apt-get update && sudo apt-get install -y git
  elif [[ -f /etc/redhat-release ]]; then
    sudo dnf install -y git || sudo yum install -y git
  elif [[ -f /etc/arch-release ]]; then
    sudo pacman -S --noconfirm git
  else
    echo "Error: Unsupported operating system. Please install Git manually."
    exit 1
  fi
else
  echo "✓ Git is already installed: $(git --version)"
fi

# -----------------------------------------------------------------------------
# 2. Validate directory and repository state
# -----------------------------------------------------------------------------
if [[ ! -d "$TARGET_DIR" ]]; then
  echo "Error: Directory '$TARGET_DIR' does not exist."
  exit 1
fi

cd "$TARGET_DIR"

if ! git rev-parse --is-inside-work-tree &> /dev/null; then
  echo "Error: Directory '$TARGET_DIR' is not a Git repository."
  exit 1
fi

# -----------------------------------------------------------------------------
# 3. Perform Git Operations
# -----------------------------------------------------------------------------
echo "Processing repository at: $(pwd)"

git add .

# Check if there are staged changes before committing
if git diff --cached --quiet; then
  echo "No changes to commit."
else
  git commit -m "$COMMIT_MSG"
  
  CURRENT_BRANCH=$(git branch --show-current)
  echo "Pushing changes to origin/$CURRENT_BRANCH..."
  git push origin "$CURRENT_BRANCH"
  echo "✓ Successfully pushed changes."
fi