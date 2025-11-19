#!/usr/bin/env python3
"""Terminate a RunPod instance."""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY')
RUNPOD_API_URL = "https://api.runpod.io/graphql"

def terminate_pod(pod_id: str):
    """Terminate a pod."""
    query = """
    mutation TerminatePod($input: PodTerminateInput!) {
        podTerminate(input: $input)
    }
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }
    
    variables = {"input": {"podId": pod_id}}
    payload = {"query": query, "variables": variables}
    
    response = requests.post(RUNPOD_API_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python terminate_pod.py <pod_id>")
        print("\nTo find pod IDs, run: python check_pod.py")
        sys.exit(1)
    
    pod_id = sys.argv[1]
    
    confirm = input(f"⚠️  Are you sure you want to terminate pod {pod_id}? (yes/no): ").strip().lower()
    
    if confirm != "yes":
        print("Cancelled.")
        sys.exit(0)
    
    print(f"🗑️  Terminating pod {pod_id}...")
    result = terminate_pod(pod_id)
    
    if 'errors' in result:
        print(f"❌ Error: {result['errors']}")
    else:
        print(f"✅ Pod terminated successfully")

