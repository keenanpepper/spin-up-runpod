#!/usr/bin/env python3
"""
RunPod Management Utility

List, inspect, and manage your RunPod instances.
"""

import os
import sys
import json
from dotenv import load_dotenv
import requests
from datetime import datetime

# Load environment variables
load_dotenv()

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
if not RUNPOD_API_KEY:
    print("❌ Error: RUNPOD_API_KEY not found in .env file")
    sys.exit(1)

RUNPOD_API_URL = "https://api.runpod.io/graphql"


def graphql_query(query, variables=None):
    """Execute a GraphQL query against RunPod API."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    response = requests.post(RUNPOD_API_URL, json=payload, headers=headers)
    response.raise_for_status()
    
    result = response.json()
    if "errors" in result:
        print(f"❌ GraphQL Error: {json.dumps(result['errors'], indent=2)}")
        raise Exception(f"GraphQL query failed: {result['errors']}")
    
    return result["data"]


def list_pods():
    """List all your pods."""
    query = """
    query {
        myself {
            pods {
                id
                name
                desiredStatus
                imageName
                machine {
                    gpuDisplayName
                }
                runtime {
                    uptimeInSeconds
                    ports {
                        ip
                        isIpPublic
                        privatePort
                        publicPort
                    }
                }
            }
        }
    }
    """
    
    data = graphql_query(query)
    pods = data["myself"]["pods"]
    
    if not pods:
        print("📭 No pods found")
        return
    
    print(f"\n📦 Your Pods ({len(pods)} total)\n")
    print("=" * 80)
    
    for pod in pods:
        print(f"\n🖥️  {pod['name']}")
        print(f"   ID: {pod['id']}")
        print(f"   Status: {pod['desiredStatus']}")
        print(f"   GPU: {pod['machine']['gpuDisplayName']}")
        print(f"   Image: {pod['imageName']}")
        
        if pod['runtime']:
            uptime_hours = pod['runtime']['uptimeInSeconds'] / 3600
            print(f"   Uptime: {uptime_hours:.1f} hours")
            
            # Find SSH port
            for port in pod['runtime']['ports']:
                if port['privatePort'] == 22 and port['isIpPublic']:
                    print(f"   SSH: {port['ip']}:{port['publicPort']}")
        else:
            print("   Runtime: Not started")
        
        print("-" * 80)


def get_pod_details(pod_id):
    """Get detailed information about a specific pod."""
    query = """
    query Pod($podId: String!) {
        pod(input: {podId: $podId}) {
            id
            name
            desiredStatus
            imageName
            env
            volumeInGb
            costPerHr
            machine {
                gpuDisplayName
                gpuCount
            }
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
    
    data = graphql_query(query, {"podId": pod_id})
    pod = data["pod"]
    
    print(f"\n📦 Pod Details: {pod['name']}\n")
    print("=" * 80)
    print(f"ID: {pod['id']}")
    print(f"Status: {pod['desiredStatus']}")
    print(f"GPU: {pod['machine']['gpuCount']}x {pod['machine']['gpuDisplayName']}")
    print(f"Cost: ${pod['costPerHr']}/hr")
    print(f"Storage: {pod['volumeInGb']} GB")
    print(f"Image: {pod['imageName']}")
    
    if pod['runtime']:
        uptime_hours = pod['runtime']['uptimeInSeconds'] / 3600
        cost_so_far = uptime_hours * pod['costPerHr']
        print(f"\nUptime: {uptime_hours:.1f} hours (${cost_so_far:.2f} so far)")
        
        print("\nPorts:")
        for port in pod['runtime']['ports']:
            if port['isIpPublic']:
                print(f"  {port['privatePort']} -> {port['ip']}:{port['publicPort']} ({port['type']})")
    
    if pod['env']:
        print(f"\nEnvironment Variables: {len(pod['env'])} set")
    
    print("=" * 80)


def stop_pod(pod_id):
    """Stop a running pod."""
    mutation = """
    mutation StopPod($podId: String!) {
        podStop(input: {podId: $podId}) {
            id
            desiredStatus
        }
    }
    """
    
    print(f"⏸️  Stopping pod {pod_id}...")
    data = graphql_query(mutation, {"podId": pod_id})
    print(f"✅ Pod stopped: {data['podStop']['desiredStatus']}")


def terminate_pod(pod_id):
    """Terminate (delete) a pod."""
    mutation = """
    mutation TerminatePod($podId: String!) {
        podTerminate(input: {podId: $podId})
    }
    """
    
    print(f"🗑️  Terminating pod {pod_id}...")
    
    # Confirm
    print("⚠️  This will permanently delete the pod (but not your network volume)")
    confirm = input("Type 'yes' to confirm: ")
    
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return
    
    graphql_query(mutation, {"podId": pod_id})
    print("✅ Pod terminated")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_pods.py list              - List all your pods")
        print("  python manage_pods.py details <pod_id>  - Show pod details")
        print("  python manage_pods.py stop <pod_id>     - Stop a pod")
        print("  python manage_pods.py terminate <pod_id> - Delete a pod")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == "list":
            list_pods()
        
        elif command == "details":
            if len(sys.argv) < 3:
                print("❌ Please provide a pod ID")
                sys.exit(1)
            get_pod_details(sys.argv[2])
        
        elif command == "stop":
            if len(sys.argv) < 3:
                print("❌ Please provide a pod ID")
                sys.exit(1)
            stop_pod(sys.argv[2])
        
        elif command == "terminate":
            if len(sys.argv) < 3:
                print("❌ Please provide a pod ID")
                sys.exit(1)
            terminate_pod(sys.argv[2])
        
        else:
            print(f"❌ Unknown command: {command}")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

