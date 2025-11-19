#!/usr/bin/env python3
"""
List Available GPU Types

Query RunPod API to see all available GPU types with their exact IDs.
"""

import os
import sys
from dotenv import load_dotenv
import requests
import json

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


def list_gpu_types():
    """List all available GPU types."""
    query = """
    query GpuTypes {
        gpuTypes {
            id
            displayName
            memoryInGb
            communityCloud
            secureCloud
        }
    }
    """
    
    data = graphql_query(query)
    gpu_types = data["gpuTypes"]
    
    print(f"\n🎮 Available GPU Types ({len(gpu_types)} total)\n")
    print("=" * 100)
    
    # Group by type
    a100_gpus = [g for g in gpu_types if "A100" in g["displayName"]]
    h100_gpus = [g for g in gpu_types if "H100" in g["displayName"]]
    rtx_gpus = [g for g in gpu_types if "RTX" in g["displayName"]]
    other_gpus = [g for g in gpu_types if g not in a100_gpus + h100_gpus + rtx_gpus]
    
    def print_gpu_section(title, gpus):
        if not gpus:
            return
        
        print(f"\n📊 {title}")
        print("-" * 100)
        
        for gpu in sorted(gpus, key=lambda x: x["displayName"]):
            print(f"\n  {gpu['displayName']}")
            print(f"    ID: {gpu['id']}")
            print(f"    Memory: {gpu['memoryInGb']} GB")
            
            clouds = []
            if gpu['communityCloud']:
                clouds.append("Community")
            if gpu['secureCloud']:
                clouds.append("Secure")
            if clouds:
                print(f"    Available: {', '.join(clouds)}")
    
    print_gpu_section("🔥 A100 GPUs", a100_gpus)
    print_gpu_section("⚡ H100 GPUs", h100_gpus)
    print_gpu_section("🎯 RTX GPUs", rtx_gpus)
    print_gpu_section("💻 Other GPUs", other_gpus)
    
    print("\n" + "=" * 100)
    print("\n💡 Tip: Copy the ID value to your YAML config's 'gpu_type' field")


def check_availability(gpu_type_id=None):
    """Check current availability of GPUs."""
    # Note: This queries for available instances
    query = """
    query GpuTypes {
        gpuTypes {
            id
            displayName
            memoryInGb
        }
    }
    """
    
    print("\n🔍 Checking GPU availability...")
    print("Note: Use RunPod web UI for real-time availability by region")
    
    data = graphql_query(query)
    gpu_types = data["gpuTypes"]
    
    if gpu_type_id:
        gpu = next((g for g in gpu_types if g["id"] == gpu_type_id), None)
        if gpu:
            print(f"\n✓ Found: {gpu['displayName']} ({gpu['id']})")
            print("  Check web UI for current availability in your region")
        else:
            print(f"\n❌ GPU type not found: {gpu_type_id}")


def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "check" and len(sys.argv) > 2:
            check_availability(sys.argv[2])
        else:
            print(f"Unknown command: {command}")
    else:
        list_gpu_types()


if __name__ == "__main__":
    main()

