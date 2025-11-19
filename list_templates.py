#!/usr/bin/env python3
"""List all available templates including RunPod official ones."""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY')
RUNPOD_API_URL = "https://api.runpod.io/graphql"

def list_all_templates():
    """Query all templates via GraphQL."""
    # Try to get user's templates
    query = """
    query {
        myself {
            podTemplates {
                id
                name
                imageName
                isPublic
            }
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
        print(f"GraphQL errors: {result['errors']}")
        return []
    
    return result.get('data', {}).get('myself', {}).get('podTemplates', [])

def search_community_templates(search_term="pytorch"):
    """Try to search community/public templates."""
    query = """
    query CommunityTemplates {
        communityTemplates {
            id
            name
            imageName
        }
    }
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }
    
    payload = {"query": query}
    
    try:
        response = requests.post(RUNPOD_API_URL, json=payload, headers=headers)
        result = response.json()
        
        if 'errors' not in result:
            return result.get('data', {}).get('communityTemplates', [])
    except Exception as e:
        print(f"Could not fetch community templates: {e}")
    
    return []

if __name__ == "__main__":
    print("📋 Your Templates:\n")
    templates = list_all_templates()
    
    if templates:
        for tpl in templates:
            print(f"  ID: {tpl['id']}")
            print(f"  Name: {tpl['name']}")
            print(f"  Image: {tpl.get('imageName', 'N/A')}")
            print(f"  Public: {tpl.get('isPublic', False)}")
            print()
    else:
        print("  No user templates found")
    
    print("\n" + "="*60)
    print("\n🌍 Searching for community templates...\n")
    
    community = search_community_templates()
    if community:
        for tpl in community[:20]:  # Show first 20
            print(f"  ID: {tpl['id']}")
            print(f"  Name: {tpl['name']}")
            print(f"  Image: {tpl.get('imageName', 'N/A')}")
            print()
    else:
        print("  Could not fetch community templates")

