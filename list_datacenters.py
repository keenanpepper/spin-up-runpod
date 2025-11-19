#!/usr/bin/env python3
"""
List Available Datacenters

Query RunPod API to see all available datacenters/regions.
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


def get_network_volumes():
    """Get user's network volumes to show their locations."""
    query = """
    query {
        myself {
            networkVolumes {
                id
                name
                dataCenterId
                size
            }
        }
    }
    """
    
    try:
        data = graphql_query(query)
        volumes = data["myself"]["networkVolumes"]
        
        if volumes:
            print("\n📦 Your Network Volumes\n")
            print("=" * 80)
            for vol in volumes:
                print(f"\n  {vol['name']}")
                print(f"    ID: {vol['id']}")
                print(f"    Datacenter: {vol['dataCenterId']}")
                print(f"    Size: {vol['size']} GB")
            print("\n" + "=" * 80)
            print("\n💡 Tip: Use the datacenter ID in your YAML config to ensure")
            print("   your pod is created in the same region as your network volume")
        else:
            print("\n📭 No network volumes found")
    except Exception as e:
        print(f"\n⚠️  Could not fetch network volumes: {e}")


def main():
    print("\n🌍 RunPod Datacenters\n")
    
    # Show user's network volumes and their locations
    get_network_volumes()
    
    print("\n" + "-" * 80)
    print("\nCommon Datacenter IDs:")
    print("  • CA-MTL-1, CA-MTL-2, CA-MTL-3  (Montreal, Canada)")
    print("  • EU-RO-1                       (Romania)")
    print("  • EU-SE-1                       (Sweden)")
    print("  • EUR-IS-1, EUR-IS-2            (Iceland)")
    print("  • US-GA-1                       (Georgia, USA)")
    print("  • US-KS-2                       (Kansas, USA)")
    print("  • US-OR-1                       (Oregon, USA)")
    print("\nNote: Datacenter availability varies by GPU type and time.")
    print("      Check the RunPod web UI for current availability.")


if __name__ == "__main__":
    main()

