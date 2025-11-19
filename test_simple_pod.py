#!/usr/bin/env python3
"""Test creating a simple pod without volume to isolate the issue."""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY')
RUNPOD_API_URL = "https://api.runpod.io/graphql"

def create_simple_pod():
    """Create a very simple pod matching the docs example."""
    query = """
    mutation CreatePod($input: PodFindAndDeployOnDemandInput!) {
        podFindAndDeployOnDemand(input: $input) {
            id
            desiredStatus
            imageName
        }
    }
    """
    
    # Use the exact format from the docs
    variables = {
        "input": {
            "cloudType": "ALL",
            "gpuCount": 1,
            "volumeInGb": 40,
            "containerDiskInGb": 40,
            "minVcpuCount": 2,
            "minMemoryInGb": 15,
            "gpuTypeId": "NVIDIA A100 80GB PCIe",
            "name": "Test Simple Pod",
            "imageName": "runpod/pytorch",
            "dockerArgs": "",
            "ports": "8888/http,22/tcp",
            "volumeMountPath": "/workspace"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }
    
    payload = {"query": query, "variables": variables}
    
    response = requests.post(RUNPOD_API_URL, json=payload, headers=headers)
    result = response.json()
    
    print("Response:")
    import json
    print(json.dumps(result, indent=2))
    
    if 'errors' in result:
        print(f"\n❌ Error: {result['errors']}")
        return None
    
    pod_data = result.get('data', {}).get('podFindAndDeployOnDemand', {})
    pod_id = pod_data.get('id')
    print(f"\n✅ Created pod: {pod_id}")
    return pod_id

if __name__ == "__main__":
    create_simple_pod()

