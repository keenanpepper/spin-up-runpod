#!/usr/bin/env python3
"""Quick script to check pod status and connection info."""

import os
import sys
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
            desiredStatus
            imageName
            runtime {
                uptimeInSeconds
                ports {
                    ip
                    isIpPublic
                    privatePort
                    publicPort
                    type
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
    response.raise_for_status()
    return response.json()

def list_my_pods():
    """List all user's pods."""
    query = """
    query {
        myself {
            pods {
                id
                name
                desiredStatus
                runtime {
                    uptimeInSeconds
                    ports {
                        ip
                        privatePort
                        publicPort
                    }
                }
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
    response.raise_for_status()
    result = response.json()
    return result.get('data', {}).get('myself', {}).get('pods', [])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Query specific pod
        pod_id = sys.argv[1]
        result = query_pod(pod_id)
        print(json.dumps(result, indent=2))
    else:
        # List all pods
        print("📋 Your running pods:\n")
        pods = list_my_pods()
        
        for pod in pods:
            print(f"Pod: {pod['name']} (ID: {pod['id']})")
            print(f"  Status: {pod.get('desiredStatus', 'UNKNOWN')}")
            
            if pod.get('runtime'):
                runtime = pod['runtime']
                uptime = runtime.get('uptimeInSeconds', 0)
                print(f"  Uptime: {uptime}s ({uptime // 60} minutes)")
                
                ports = runtime.get('ports', [])
                for port in ports:
                    if port['privatePort'] == 22:
                        print(f"  SSH: {port['ip']}:{port['publicPort']}")
            else:
                print(f"  ⚠️  No runtime info (pod may be starting)")
            
            print()

