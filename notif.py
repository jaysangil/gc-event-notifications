from dotenv import load_dotenv
load_dotenv()

from PureCloudPlatformClientV2.rest import ApiException
import PureCloudPlatformClientV2
import websockets
import asyncio
import sys
import os
import json


print("\n-----------------------------------------------------")
print("--- Genesys Cloud Python SDK Notification Service ---")
print("-----------------------------------------------------")
print("\nYou can exit the application at anytime with Ctrl-c..")

CLIENT_ID     = os.environ["GC_CLIENT_ID"]
CLIENT_SECRET = os.environ["GC_CLIENT_SECRET"]
ENVIRONMENT   = os.environ["GC_ENVIRONMENT"]  
USER_ID       = os.environ["GC_TARGET_USER"]

missing = [name for name, val in {
    "GC_CLIENT_ID": CLIENT_ID,
    "GC_CLIENT_SECRET": CLIENT_SECRET,
    "GC_ENVIRONMENT": ENVIRONMENT,
    "GC_TARGET_USER": USER_ID}.items() if not val]
if missing:
    print(f"Error: Missing environmental variable(s): {', '.join(missing)}")
    sys.exit(1)
print("✔️  All required environment variables loaded.\n")

# --- Create notification channel ---

def create_notifications_channel(notifications_api):
    try:
        print("\nCreating notifications channel…")
        return notifications_api.post_notifications_channels()
    except ApiException as e:
        print(f"Exception when creating channel: {e}")
        sys.exit(1)
        
# --- Subscribe to users topic ---

def subscribe_to_topic(user_id, channel_id, notifications_api):
    topic = f"v2.users.{user_id}.conversations"
    body = [{ "id": topic }]
    try:
        print(f"\nSubscribing to {topic}…")
        notifications_api.put_notifications_channel_subscriptions(channel_id, body)
    except ApiException as e:
        print(f"Exception when subscribing to {topic}: {e}")
        sys.exit(1)
        
# --- Listen for incoming WebSocket messages ---

async def listen(uri, user_id):
    print("\nOpening WebSocket connection…")
    async with websockets.connect(uri) as ws:
        print(f"\nConnected! Listening for conversation events for user {user_id}\n")
        async for msg in ws:
            obj = json.loads(msg)
            print(json.dumps(obj, indent=4))
            
# --- Orchestration ---

def main():
    # 5.1) Tell the SDK which region to hit
    PureCloudPlatformClientV2.configuration.host = f"https://api.{ENVIRONMENT}"

    # 5.2) Authenticate and get a ready-to-go ApiClient
    api_client = PureCloudPlatformClientV2.ApiClient() \
        .get_client_credentials_token(CLIENT_ID, CLIENT_SECRET)

    # 5.3) Spin up the Notifications API
    notifications_api = PureCloudPlatformClientV2.NotificationsApi(api_client)

    # 5.4) Create channel & subscribe
    channel = create_notifications_channel(notifications_api)
    uri, channel_id = channel.connect_uri, channel.id
    subscribe_to_topic(USER_ID, channel_id, notifications_api)

    # 5.5) Start listening
    asyncio.get_event_loop().run_until_complete(listen(uri, USER_ID))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\Closing...")
        sys.exit(0)