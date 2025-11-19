#!/usr/bin/env python3
"""Get SSH keys from RunPod account."""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY')
RUNPOD_API_URL = "https://api.runpod.io/graphql"

def get_my_ssh_keys():
    """Query user's SSH keys."""
    query = """
    query {
        myself {
            pubKey
        }
    }
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }
    
    payload = {"query": query}
    
    response = requests.post(RUNPOD_API_URL, json=payload, headers=headers)
    result = response.json()
    
    if 'errors' in result:
        print(f"Errors: {result['errors']}")
        return None
    
    return result.get('data', {}).get('myself', {}).get('pubKey')

if __name__ == "__main__":
    keys = get_my_ssh_keys()
    if keys:
        print("Your SSH keys:")
        print(keys)
    else:
        print("No SSH keys found")

