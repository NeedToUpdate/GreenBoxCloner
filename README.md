# Git Confidential Cloner

This Python script allows you to clone a Git repository, anonymizing all data while keeping the commit history intact. The script replaces all file content, commit messages, author names, author emails, branch names, and tag names, except
for a specified author's name and email. This could be useful for maintaining your green boxes on GitHub, while keeping the actual work confidential.

## Features

- Anonymizes author names and emails (except for one specified author)
- Replaces all file content with commit hashes
- Anonymizes branch and tag names
- Anonymizes commit messages
- Preserves commit dates and parents, so the commit graph remains the same

## Example of new history created

<img src="./expunged_history.jpg" width="700" />

---

## Installation

Firstly, clone this repository and navigate into it:

```bash
git clone https://github.com/NeedToUpdate/git-confidential-cloner.git
cd git-confidential-cloner
```

It's recommended to use a virtual environment to isolate your Python dependencies. Here's how you can do it:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

Then, install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

You can run the script using the following command:

```bash
python clone.py --source /path/to/source --dest /path/to/destination --author_name "Your Name" --author_email "Your Email"
```

### Arguments

- `--source`: Path to the source repository (required)
- `--dest`: Path to the destination repository (required)
- `--author_name`: Author name to be preserved (required)
- `--author_email`: Author email to be preserved (required)
- `--replace_name`: Replacement for other author names (optional)
- `--replace_email`: Replacement for other author emails (optional)
- `--expunged_name`: The name set to everyone else in the repo (optional, default: "[Expunged]")
- `--expunged_email`: The email set to everyone else in the repo (optional, default: "expunged@email.com")
- `--expunged_commit`: The message set for every commit (optional, default: "[commit message removed for confidentiality]")
- `--expunged_branch`: The branch name prefix, each branch will end with its index number (optional, default: "expunged-branch-")
- `--expunged_tag`: The tag name prefix, each tag will end with its index number (optional, default: "expunged-tag-")

---

## License

This project is licensed under the terms of the MIT license.

---
