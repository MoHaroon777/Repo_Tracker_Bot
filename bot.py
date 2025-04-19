import discord
from discord.ext import tasks
import requests
import os
import datetime
import logging
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()  # Load environment variables from .env file

BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')
GITHUB_REPO = os.getenv('GITHUB_REPO_NAME')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN') # Optional: For higher rate limits / private repos
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL_SECONDS', 300)) # Default to 300 seconds (5 minutes)

# --- Setup Logging ---
# Basic logging to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')
logger = logging.getLogger('discord') # Get logger for discord.py itself
logger.setLevel(logging.INFO) # Or DEBUG for more verbosity
handler = logging.FileHandler(filename='discord_bot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# --- Global State ---
# Stores the SHA of the last commit we notified about
last_known_commit_sha = None

# --- Bot Setup ---
# Define intents - necessary for receiving certain events
intents = discord.Intents.default()
# No specific intents needed for just sending messages and running tasks,
# but defaults are usually fine. If you add commands later, you might need message_content=True

bot = discord.Client(intents=intents) # Using Client as we don't need command prefix features here

# --- GitHub API Interaction ---
def get_latest_commit():
    """Fetches the latest commit from the specified GitHub repository."""
    global last_known_commit_sha # Allow modification of the global variable

    api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/commits?per_page=1"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        response = requests.get(api_url, headers=headers, timeout=10) # 10 second timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        data = response.json()
        if not data:
            logger.warning(f"No commits found for {GITHUB_USERNAME}/{GITHUB_REPO}. Is the repository empty or name correct?")
            return None, None # Return None if repo is empty or has no commits

        latest_commit = data[0] # Get the first commit from the list (which is the latest)
        return latest_commit['sha'], latest_commit # Return SHA and the full commit object

    except requests.exceptions.Timeout:
        logger.error("Request to GitHub API timed out.")
        return None, None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching GitHub data: {e}")
        # Specific check for 404 Not Found
        if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
             logger.error(f"Repository {GITHUB_USERNAME}/{GITHUB_REPO} not found. Check USERNAME and REPO_NAME.")
        # Specific check for 403 Forbidden (often rate limit or auth issue)
        elif hasattr(e, 'response') and e.response is not None and e.response.status_code == 403:
             logger.error("Access forbidden (403). Check GITHUB_TOKEN permissions or API rate limits.")
             # You might want to check response headers for rate limit info if available
             rate_limit_remaining = e.response.headers.get('X-RateLimit-Remaining')
             rate_limit_reset = e.response.headers.get('X-RateLimit-Reset')
             if rate_limit_remaining == '0' and rate_limit_reset:
                 reset_time = datetime.datetime.fromtimestamp(int(rate_limit_reset)).strftime('%Y-%m-%d %H:%M:%S UTC')
                 logger.warning(f"GitHub API rate limit likely exceeded. Resets at: {reset_time}")

        return None, None
    except Exception as e:
        logger.exception(f"An unexpected error occurred in get_latest_commit: {e}") # Log full traceback
        return None, None


# --- Discord Bot Events & Tasks ---
@bot.event
async def on_ready():
    """Event handler for when the bot logs in and is ready."""
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info(f'Monitoring GitHub Repo: {GITHUB_USERNAME}/{GITHUB_REPO}')
    logger.info(f'Notifications will be sent to Channel ID: {CHANNEL_ID}')
    logger.info(f'Check interval: {CHECK_INTERVAL} seconds')
    logger.info('------')
    # Start the background task
    check_github_commits.start()

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_github_commits():
    """Background task that periodically checks for new commits."""
    global last_known_commit_sha
    logger.info("Checking for new commits...")

    current_sha, commit_data = get_latest_commit()

    if current_sha is None:
        # Error occurred or repo empty, already logged in get_latest_commit
        return

    # Initialize last_known_commit_sha on the first successful run
    if last_known_commit_sha is None:
        logger.info(f"Initial check complete. Setting baseline commit SHA: {current_sha[:7]}")
        last_known_commit_sha = current_sha
        return

    # Check if the latest commit is different from the last known one
    if current_sha != last_known_commit_sha:
        logger.info(f"New commit detected! SHA: {current_sha[:7]}")

        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            try:
                # Format the commit data into an embed
                embed = discord.Embed(
                    title=f"🚀 New Commit Pushed to `{GITHUB_REPO}`",
                    color=discord.Color.green(), # Or discord.Color.from_rgb(r, g, b)
                    url=commit_data['html_url'], # Link the title to the commit page
                    timestamp=datetime.datetime.fromisoformat(commit_data['commit']['committer']['date'].replace('Z', '+00:00')) # Parse ISO 8601 timestamp
                )

                # Author info (try committer first, fallback to author)
                committer_name = commit_data['commit']['committer']['name']
                committer_login = commit_data.get('committer', {}).get('login', 'N/A') # Login might not always be present
                committer_url = commit_data.get('committer', {}).get('html_url', None)
                committer_icon = commit_data.get('committer', {}).get('avatar_url', None)

                author_name = commit_data['commit']['author']['name']
                author_login = commit_data.get('author', {}).get('login', 'N/A')

                if committer_icon:
                    embed.set_thumbnail(url=committer_icon) # Show committer avatar

                # Commit message - keep it concise
                commit_message = commit_data['commit']['message']
                if len(commit_message) > 1000: # Embed description limit is 4096, but keep it reasonable
                    commit_message = commit_message[:1000] + "..."
                embed.description = commit_message

                # Fields for more details
                embed.add_field(name="Committer", value=f"[{committer_name} ({committer_login})]({committer_url})" if committer_url else f"{committer_name} ({committer_login})", inline=True)
                # Only show author if different from committer
                if author_name != committer_name or author_login != committer_login:
                     embed.add_field(name="Author", value=f"{author_name} ({author_login})", inline=True)

                embed.add_field(name="Commit Hash", value=f"[`{current_sha[:7]}`]({commit_data['html_url']})", inline=False) # Link short SHA

                embed.set_footer(text=f"Repository: {GITHUB_USERNAME}/{GITHUB_REPO}")

                await channel.send(embed=embed)
                logger.info(f"Notification sent to channel {CHANNEL_ID} for commit {current_sha[:7]}")

                # Update the last known SHA *after* successful notification
                last_known_commit_sha = current_sha

            except discord.errors.Forbidden:
                logger.error(f"Permission error: Cannot send messages to channel {CHANNEL_ID}. Check bot permissions.")
            except discord.errors.NotFound:
                logger.error(f"Channel {CHANNEL_ID} not found. Check DISCORD_CHANNEL_ID.")
            except Exception as e:
                logger.exception(f"An unexpected error occurred while sending Discord message: {e}") # Log full traceback

        else:
            logger.error(f"Could not find channel with ID: {CHANNEL_ID}. Make sure the ID is correct and the bot is in the server.")
            # Optional: Stop the task if channel is invalid?
            # check_github_commits.stop()

    else:
        logger.info("No new commits found.")

@check_github_commits.before_loop
async def before_check():
    """Executed once before the task loop starts."""
    await bot.wait_until_ready() # Wait for the bot to be fully connected
    logger.info("Bot is ready, starting GitHub commit check loop...")
    # Perform an initial check without sending notification to set the baseline
    global last_known_commit_sha
    logger.info("Performing initial commit check to set baseline...")
    initial_sha, _ = get_latest_commit()
    if initial_sha:
        last_known_commit_sha = initial_sha
        logger.info(f"Baseline commit SHA set to: {last_known_commit_sha[:7]}")
    else:
         logger.warning("Could not fetch initial commit to set baseline. Will retry on next loop interval.")


# --- Run the Bot ---
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Error: DISCORD_BOT_TOKEN not found in environment variables.")
    elif not CHANNEL_ID:
        print("Error: DISCORD_CHANNEL_ID not found in environment variables.")
    elif not GITHUB_USERNAME or not GITHUB_REPO:
        print("Error: GITHUB_USERNAME or GITHUB_REPO_NAME not found in environment variables.")
    else:
        try:
            bot.run(BOT_TOKEN, log_handler=None) # Use our custom logging setup
        except discord.errors.LoginFailure:
             logger.error("Login failed: Invalid Discord Bot Token provided.")
        except Exception as e:
             logger.exception(f"Fatal error during bot execution: {e}")