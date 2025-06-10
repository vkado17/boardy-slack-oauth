import os
from flask import Flask, request, redirect
import requests
from dotenv import load_dotenv
from notion_client import Client as NotionClient

load_dotenv()
app = Flask(__name__)

# Slack
CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SLACK_REDIRECT_URI")

# Notion
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ID = os.getenv("NOTION_DB_ID")
notion = NotionClient(auth=NOTION_TOKEN)

# Step 1: Auth link
@app.route("/")
def home():
    return f'''
    <a href="https://slack.com/oauth/v2/authorize?client_id={CLIENT_ID}&scope=users.profile:read,users.profile:write&user_scope=users.profile:read,users.profile:write&redirect_uri={REDIRECT_URI}">
        Connect your Slack
    </a>
    '''

# Step 2: Callback
@app.route("/slack/oauth/callback")
def oauth_callback():
    code = request.args.get("code")
    if not code:
        return "No code provided", 400

    # Exchange code for token
    res = requests.post("https://slack.com/api/oauth.v2.access", data={
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI
    }).json()

    user_token = res.get("authed_user", {}).get("access_token")
    slack_user_id = res.get("authed_user", {}).get("id")

    if not user_token or not slack_user_id:
        return f"Failed to get Slack token: {res}"

    print(f"✅ Slack user ID: {slack_user_id}")
    print(f"🔐 Access token: {user_token}")

    # Search Notion DB for matching Slack ID
    db_results = notion.databases.query(database_id=NOTION_DB_ID, filter={
        "property": "Slack ID",
        "rich_text": {
            "equals": slack_user_id
        }
    })

    if not db_results["results"]:
        return f"❌ Slack ID {slack_user_id} not found in Notion database", 404

    # Update the matching page
    page_id = db_results["results"][0]["id"]
    try:
        notion.pages.update(page_id=page_id, properties={
            "User Token": {
                "rich_text": [{
                    "text": {"content": user_token}
                }]
            }
        })
        print(f"✅ Updated Notion page {page_id} with token")
        return "✅ Success! Your Slack has been connected."
    except Exception as e:
        return f"❌ Failed to update Notion: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
