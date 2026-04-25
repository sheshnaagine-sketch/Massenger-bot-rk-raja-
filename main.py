import requests
import json
import time

"""
Facebook Graph API Integration Script
--------------------------------------
This script demonstrates how to interact with the Facebook Graph API using 
a User Access Token. 

Prerequisites:
1. A Facebook Developer Account.
2. A registered App in the Meta for Developers portal.
3. A 'User Access Token' from the Graph API Explorer.
   Link: https://developers.facebook.com/tools/explorer/
"""

class FacebookBot:
    def __init__(self, access_token):
        self.base_url = "https://graph.facebook.com/v18.0"
        self.access_token = access_token

    def _get_request(self, endpoint, params=None):
        """Internal helper for GET requests with exponential backoff."""
        if params is None:
            params = {}
        params['access_token'] = self.access_token
        
        url = f"{self.base_url}/{endpoint}"
        
        retries = 0
        max_retries = 5
        backoff = 1 # seconds

        while retries < max_retries:
            try:
                response = requests.get(url, params=params)
                data = response.json()
                
                if response.status_code == 200:
                    return data
                else:
                    print(f"API Error: {data.get('error', {}).get('message', 'Unknown Error')}")
                    return None
            except Exception as e:
                print(f"Connection error: {e}")
            
            retries += 1
            time.sleep(backoff)
            backoff *= 2 # Exponential backoff
            
        return None

    def _post_request(self, endpoint, data=None):
        """Internal helper for POST requests."""
        if data is None:
            data = {}
        data['access_token'] = self.access_token
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.post(url, data=data)
            return response.json()
        except Exception as e:
            print(f"Request failed: {e}")
            return None

    def get_me(self):
        """Fetch basic profile info of the token owner."""
        print("Fetching profile info...")
        return self._get_request("me", {"fields": "id,name,email"})

    def get_my_posts(self):
        """Fetch the last 5 posts from the user's feed."""
        print("Fetching recent posts...")
        return self._get_request("me/feed", {"limit": 5})

    def post_status(self, message):
        """
        Post a status update. 
        Requires 'publish_video' or 'pages_manage_posts' permissions depending on target.
        """
        print(f"Attempting to post: {message}")
        return self._post_request("me/feed", {"message": message})

def main():
    # --- CONFIGURATION ---
    # Replace with your actual token from https://developers.facebook.com/tools/explorer/
    USER_TOKEN = "" 

    if not USER_TOKEN:
        print("Error: Please provide a valid User Access Token in the script.")
        return

    bot = FacebookBot(USER_TOKEN)

    # 1. Get Profile Information
    profile = bot.get_me()
    if profile:
        print(f"Logged in as: {profile.get('name')} (ID: {profile.get('id')})")

    # 2. Get Feed
    feed = bot.get_my_posts()
    if feed and 'data' in feed:
        print("\nYour last few posts:")
        for post in feed['data']:
            print(f"- {post.get('created_time')}: {post.get('message', '[No Text]')}")

    # 3. Post a message (Requires specific permissions)
    # result = bot.post_status("Hello from Python script!")
    # print(result)

if __name__ == "__main__":
    main()
