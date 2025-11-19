#!/usr/bin/env python3
"""Quick script to query existing pod configuration."""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY')
RUNPOD_API_URL = "https://api.runpod.io/graphql"

def query_pod(pod_id: str):
    """Get full information about a pod."""
    query = """
    query Pod($input: PodFilter!) {
        pod(input: $input) {
            id
            name
            imageName
            containerDiskInGb
            volumeInGb
            machine {
                gpuDisplayName
            }
            gpuCount
            cloudType
            volumeKey
            env
            ports
            desiredStatus
            runtime {
                ports {
                    ip
                    privatePort
                    publicPort
                }
            }
        }
    }
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }
    
    variables = {"input": {"podId": pod_id}}
    payload = {"query": query, "variables": variables}
    
    response = requests.post(RUNPOD_API_URL, json=payload, headers=headers)
    result = response.json()
    if response.status_code != 200 or 'errors' in result:
        print(f"Error response: {json.dumps(result, indent=2)}")
    response.raise_for_status()
    return result

if __name__ == "__main__":
    result = query_pod("svjarx90ypvnc0")
    print(json.dumps(result, indent=2))

