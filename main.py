import os
from flask import Flask, request, redirect
import requests
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SLACK_REDIRECT_URI")

# STEP 1: Auth URL for users to click
@app.route("/")
def home():
    return f'''
    <a href="https://slack.com/oauth/v2/authorize?client_id={CLIENT_ID}&scope=users.profile:read,users.profile:write&user_scope=users.profile:read,users.profile:write&redirect_uri={REDIRECT_URI}">
        Connect your Slack
    </a>
    '''

# STEP 2: Handle OAuth Callback
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

    # You should store this securely (e.g., in Supabase, Google Sheets, etc.)
    print(f"✅ Received user token for {slack_user_id}: {user_token}")

    return f"Thanks! You're connected."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
