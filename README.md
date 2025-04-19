# Repo Tracker Bot 🤖

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
<!-- Add other badges if you set up CI/CD, etc. -->

A Python-based Discord bot that monitors a specific GitHub repository for new commits and sends informative notifications to a designated Discord channel. Keep your team or yourself updated on the latest code changes automatically!

![Example Notification Placeholder](https://via.placeholder.com/600x200/cccccc/969696.png?text=Example+Discord+Notification+Embed)
*(Replace the placeholder above with an actual screenshot of the bot's notification embed)*

---

## ✨ Features

*   **🚀 GitHub Repository Monitoring:** Tracks a specific public or private GitHub repository.
*   **🔔 New Commit Notifications:** Sends a message to a Discord channel when a new commit is detected on the default branch.
*   **✨ Informative Embeds:** Uses Discord embeds to display commit details nicely, including:
    *   Commit message (truncated if too long)
    *   Committer's name and GitHub profile link
    *   Commit hash (shortened) linked to the commit page on GitHub
    *   Timestamp of the commit
    *   Author details (if different from the committer)
    *   Committer's avatar
*   **⏱️ Periodic Checking:** Checks GitHub for updates at a user-defined interval.
*   **🧠 State Management:** Remembers the last notified commit SHA to avoid sending duplicate notifications, even after bot restarts.
*   **⚙️ Easy Configuration:** Uses a `.env` file to securely manage sensitive information like tokens and configuration settings.
*   **🛡️ Robust:** Includes basic error handling for GitHub API requests and Discord interactions.
*   **📄 Logging:** Logs activity and potential errors to the console and a `discord_bot.log` file for easier debugging.

---

## Prerequisites

Before you begin, ensure you have the following:

1.  **Python:** Version 3.8 or higher installed.
2.  **Discord Bot Account:**
    *   Create one via the [Discord Developer Portal](https://discord.com/developers/applications).
    *   Obtain the **Bot Token**.
    *   Enable **Server Members Intent** and **Message Content Intent** under Privileged Gateway Intents in your Bot's settings.
3.  **Discord Server & Channel:**
    *   A Discord server where you have permission to add bots.
    *   The **Channel ID** of the channel where notifications should be sent (Enable Developer Mode in Discord to copy IDs).
4.  **GitHub Repository Details:**
    *   The **username** or **organization name** owning the repository.
    *   The **repository name** you want to monitor.
5.  **(Optional but Recommended) GitHub Personal Access Token (PAT):**
    *   Generate one from [GitHub Developer Settings](https://github.com/settings/tokens).
    *   Grant the `repo` scope (or at least `public_repo` for public repos).
    *   *This is needed for private repositories and significantly increases the API rate limit for public ones.*

---

## 🛠️ Setup & Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/YOUR_GITHUB_USERNAME/repo_tracker_bot.git
    cd repo_tracker_bot
    ```
    *(Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username)*

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Ensure you have created a `requirements.txt` file - see below)*

3.  **Create `requirements.txt` file:**
    Create a file named `requirements.txt` in the project root with the following content:
    ```txt
    discord.py>=2.0.0 # Use the latest stable version
    python-dotenv
    requests
    ```

4.  **Configure Environment Variables:**
    *   Create a file named `.env` in the root directory of the project.
    *   **Important:** Add `.env` to your `.gitignore` file to prevent accidentally committing your secrets!
    *   Populate the `.env` file with your details (see Configuration section below).

5.  **Invite the Bot:**
    *   Go to your bot's application page on the Discord Developer Portal -> OAuth2 -> URL Generator.
    *   Select the `bot` scope.
    *   Under "Bot Permissions," grant `Send Messages` and `Embed Links`.
    *   Copy the generated URL, paste it into your browser, and invite the bot to your desired server.

---

## ⚙️ Configuration (`.env` file)

Create a `.env` file in the project's root directory and add the following, replacing the placeholder values:

```dotenv
# .env Example

# --- Discord ---
DISCORD_BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN_HERE
DISCORD_CHANNEL_ID=YOUR_DISCORD_CHANNEL_ID_HERE

# --- GitHub ---
GITHUB_USERNAME=target_github_username_or_org
GITHUB_REPO_NAME=target_github_repo_name
# Optional: Highly recommended for rate limits / required for private repos
GITHUB_TOKEN=YOUR_GITHUB_PAT_HERE

# --- Bot Settings ---
# How often to check GitHub (in seconds). 300 = 5 minutes
CHECK_INTERVAL_SECONDS=300

```
⚠️ Security Note: Never share your DISCORD_BOT_TOKEN or GITHUB_TOKEN. Keep the .env file private and ensure it's listed in your .gitignore file.

## ▶️ Running the Bot
Once configured, you can run the bot using:

```bash
python bot.py
```

The bot will log in to Discord, perform an initial check to establish the current latest commit, and then start periodically checking for new commits based on your CHECK_INTERVAL_SECONDS.

## 🤝 Contributing
Contributions are welcome! If you have suggestions for improvements or find a bug, please feel free to:

1. Fork the repository.
2. Create a new branch (git checkout -b feature/YourFeature or bugfix/YourBugfix).
Make your changes.
3. Commit your changes (git commit -m 'Add some feature').
4. Push to the branch (git push origin feature/YourFeature).
5. Open a Pull Request.

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
