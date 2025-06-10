import os
from flask import Flask, request
import requests
from dotenv import load_dotenv
from notion_client import Client as NotionClient

# Load env vars
load_dotenv()
app = Flask(__name__)

# Slack OAuth Config
CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SLACK_REDIRECT_URI")

# Notion Config
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ID = os.getenv("NOTION_DB_ID")
notion = NotionClient(auth=NOTION_TOKEN)

# STEP 1: Homepage with auth link
@app.route("/")
def home():
    return f'''
    <a href="https://slack.com/oauth/v2/authorize?client_id={CLIENT_ID}&scope=users.profile:read,users.profile:write&user_scope=users.profile:read,users.profile:write&redirect_uri={REDIRECT_URI}">
        Connect your Slack
    </a>
    '''

# STEP 2: OAuth Callback
@app.route("/slack/oauth/callback")
def oauth_callback():
    code = request.args.get("code")
    if not code:
        return "No code provided", 400

    res = requests.post("https://slack.com/api/oauth.v2.access", data={
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI
    }).json()

    user_token = res.get("authed_user", {}).get("access_token")
    slack_user_id = res.get("authed_user", {}).get("id")

    if not user_token or not slack_user_id:
        return f"Failed to fetch token: {res}"

    store_user_token(slack_user_id, user_token)
    return f"✅ Thanks! You're connected as {slack_user_id}."

# STEP 3: Store token in Notion
def store_user_token(slack_user_id, token):
    try:
        pages = notion.databases.query(database_id=NOTION_DB_ID)["results"]
        for page in pages:
            props = page["properties"]
            id_field = props.get("userID", {}).get("rich_text", [])
            if id_field and id_field[0]["text"]["content"] == slack_user_id:
                notion.pages.update(
                    page_id=page["id"],
                    properties={
                        "User Token": {
                            "rich_text": [{"text": {"content": token}}]
                        }
                    }
                )
                print(f"✅ Token saved for {slack_user_id}")
                return
        print(f"⚠️ Slack ID {slack_user_id} not found in Notion.")
    except Exception as e:
        print(f"❌ Error updating Notion: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
