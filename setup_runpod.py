#!/usr/bin/env python3
"""
Simple RunPod automation script.
Creates a pod, updates SSH config, and sets up the Python environment.
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from typing import Optional
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY')
if not RUNPOD_API_KEY:
    print("❌ Error: RUNPOD_API_KEY not found in .env file")
    sys.exit(1)

# Configuration
RUNPOD_API_URL = "https://api.runpod.io/graphql"
SSH_CONFIG_PATH = Path.home() / ".ssh" / "config"


def runpod_api_call(query: str, variables: Optional[dict] = None) -> dict:
    """Make a GraphQL API call to RunPod."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    response = requests.post(RUNPOD_API_URL, json=payload, headers=headers)
    result = response.json()
    
    # Check for GraphQL errors
    if 'errors' in result:
        error_msg = result['errors'][0].get('message', 'Unknown error')
        raise Exception(f"GraphQL error: {error_msg}")
    
    response.raise_for_status()
    return result


def list_gpu_types():
    """List available GPU types."""
    query = """
    query GpuTypes {
        gpuTypes {
            id
            displayName
            memoryInGb
        }
    }
    """
    result = runpod_api_call(query)
    return result.get('data', {}).get('gpuTypes', [])


def find_gpu_type_id(display_name: str) -> Optional[str]:
    """Find GPU type ID by display name."""
    gpu_types = list_gpu_types()
    for gpu in gpu_types:
        if display_name.lower() in gpu['displayName'].lower():
            return gpu['id']
    return None


def list_templates():
    """List available RunPod templates using REST API."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }
    
    # Use REST API to get templates
    # Include RunPod official templates
    url = "https://api.runpod.io/v1/user/templates?includeRunpodTemplates=true"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result if isinstance(result, list) else []
    except Exception as e:
        print(f"   Warning: Could not fetch templates: {e}")
        return []


def find_template_by_name(name: str) -> Optional[str]:
    """Find template ID by name (partial match)."""
    templates = list_templates()
    name_lower = name.lower()
    
    # Try exact match first
    for template in templates:
        if template['name'].lower() == name_lower:
            return template['id']
    
    # Try partial match
    for template in templates:
        if name_lower in template['name'].lower():
            print(f"   Found template: {template['name']} (ID: {template['id']})")
            return template['id']
    
    return None


def get_my_ssh_keys() -> Optional[str]:
    """Get user's SSH public keys from RunPod account."""
    query = """
    query {
        myself {
            pubKey
        }
    }
    """
    
    try:
        result = runpod_api_call(query)
        return result.get('data', {}).get('myself', {}).get('pubKey')
    except Exception as e:
        print(f"   Warning: Could not fetch SSH keys: {e}")
        return None


def create_pod(name: str, gpu_type: str, gpu_count: int, volume_id: Optional[str], disk_size: int, 
               image_name: Optional[str] = None, template_id: Optional[str] = None):
    """Create a new RunPod instance."""
    print(f"🚀 Creating pod '{name}' with {gpu_count}x {gpu_type}...")
    
    # Get SSH keys from account
    print("🔑 Fetching SSH keys from account...")
    ssh_keys = get_my_ssh_keys()
    if not ssh_keys:
        print("⚠️  Warning: No SSH keys found. You may not be able to connect via SSH!")
    
    query = """
    mutation CreatePod($input: PodFindAndDeployOnDemandInput!) {
        podFindAndDeployOnDemand(input: $input) {
            id
            desiredStatus
            imageName
            machineId
            machine {
                gpuDisplayName
            }
        }
    }
    """
    
    # Build base input
    input_data = {
        "cloudType": "ALL",
        "gpuCount": gpu_count,
        "gpuTypeId": gpu_type,
        "name": name,
    }
    
    # Always add SSH keys as environment variable
    env_vars = []
    if ssh_keys:
        env_vars.append({"key": "PUBLIC_KEY", "value": ssh_keys})
    
    # Use template if specified, otherwise use image name
    if template_id:
        input_data["templateId"] = template_id
        print(f"   Using template ID: {template_id}")
        # Add SSH keys to env (templates may have default env vars but we need to add ours)
        if env_vars:
            input_data["env"] = env_vars
    elif image_name:
        input_data["imageName"] = image_name
        input_data["dockerArgs"] = ""
        input_data["env"] = env_vars
        input_data["containerDiskInGb"] = disk_size
        input_data["volumeInGb"] = 0
        input_data["ports"] = "22/tcp,8888/http"
        input_data["minVcpuCount"] = 2
        input_data["minMemoryInGb"] = 15
    else:
        raise ValueError("Either template_id or image_name must be specified")
    
    # Add network volume if specified
    if volume_id:
        input_data["networkVolumeId"] = volume_id
        # Don't need to specify volumeMountPath when using networkVolumeId
        # The template defines the mount path (default /workspace)
    
    variables = {"input": input_data}
    
    result = runpod_api_call(query, variables)
    
    if 'errors' in result:
        print(f"❌ Error creating pod: {result['errors']}")
        return None
    
    pod_data = result.get('data', {}).get('podFindAndDeployOnDemand', {})
    pod_id = pod_data.get('id')
    
    print(f"✅ Pod created with ID: {pod_id}")
    return pod_id


def get_pod_info(pod_id: str) -> dict:
    """Get information about a specific pod."""
    query = """
    query Pod($input: PodFilter!) {
        pod(input: $input) {
            id
            name
            desiredStatus
            runtime {
                uptimeInSeconds
                ports {
                    ip
                    privatePort
                    publicPort
                    type
                }
            }
        }
    }
    """
    
    variables = {"input": {"podId": pod_id}}
    result = runpod_api_call(query, variables)
    return result.get('data', {}).get('pod')


def wait_for_pod_ready(pod_id: str, timeout: int = 600) -> Optional[dict]:
    """Wait for pod to be ready and return connection info."""
    print("⏳ Waiting for pod to be ready...")
    print("   (This can take 2-5 minutes while GPU is allocated and container starts)")
    
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < timeout:
        pod_info = get_pod_info(pod_id)
        
        if pod_info:
            current_status = pod_info.get('desiredStatus', 'UNKNOWN')
            
            # Print status changes
            if current_status != last_status:
                elapsed = int(time.time() - start_time)
                print(f"\n   [{elapsed}s] Status: {current_status}")
                last_status = current_status
            
            # Check if pod has runtime (is actually running)
            if pod_info.get('runtime'):
                runtime = pod_info['runtime']
                ports = runtime.get('ports', [])
                
                # Find SSH port (port 22)
                ssh_port_info = next((p for p in ports if p['privatePort'] == 22), None)
                
                if ssh_port_info and ssh_port_info.get('publicPort'):
                    # Test if SSH is actually accepting connections
                    print(f"\n   Pod has network connectivity, testing SSH...")
                    
                    # Try to connect to SSH port
                    import socket
                    max_ssh_wait = 60  # Wait up to 60 seconds for SSH
                    ssh_ready = False
                    
                    for attempt in range(max_ssh_wait // 5):
                        try:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(5)
                            result = sock.connect_ex((ssh_port_info['ip'], ssh_port_info['publicPort']))
                            sock.close()
                            
                            if result == 0:
                                ssh_ready = True
                                break
                        except:
                            pass
                        
                        print(".", end="", flush=True)
                        time.sleep(5)
                    
                    if ssh_ready:
                        print(f"\n✅ Pod is ready and SSH is accepting connections!")
                        return {
                            'ip': ssh_port_info['ip'],
                            'port': ssh_port_info['publicPort'],
                            'name': pod_info['name']
                        }
                    else:
                        print(f"\n⚠️  Pod is up but SSH not responding yet, continuing to wait...")
        
        print(".", end="", flush=True)
        time.sleep(5)
    
    print("\n❌ Timeout waiting for pod to be ready")
    return None


def update_ssh_config(host_name: str, ip: str, port: int):
    """Update SSH config with new pod information."""
    print(f"📝 Updating SSH config for host '{host_name}'...")
    
    # Read existing config
    if SSH_CONFIG_PATH.exists():
        with open(SSH_CONFIG_PATH, 'r') as f:
            config_lines = f.readlines()
    else:
        config_lines = []
    
    # Check if host already exists
    host_exists = False
    new_lines = []
    skip_next_lines = 0
    
    for i, line in enumerate(config_lines):
        if skip_next_lines > 0:
            skip_next_lines -= 1
            continue
            
        if line.strip().startswith(f"Host {host_name}"):
            host_exists = True
            # Replace the existing host entry
            new_lines.append(f"Host {host_name}\n")
            new_lines.append(f"    HostName {ip}\n")
            new_lines.append(f"    Port {port}\n")
            new_lines.append(f"    User root\n")
            new_lines.append(f"    IdentityFile ~/.ssh/id_ed25519\n")
            new_lines.append(f"    StrictHostKeyChecking accept-new\n")
            
            # Skip the next 4-5 lines (old host config)
            j = i + 1
            while j < len(config_lines) and config_lines[j].startswith('    '):
                skip_next_lines += 1
                j += 1
        else:
            new_lines.append(line)
    
    # If host doesn't exist, add it
    if not host_exists:
        if new_lines and not new_lines[-1].endswith('\n\n'):
            new_lines.append('\n')
        new_lines.append(f"Host {host_name}\n")
        new_lines.append(f"    HostName {ip}\n")
        new_lines.append(f"    Port {port}\n")
        new_lines.append(f"    User root\n")
        new_lines.append(f"    IdentityFile ~/.ssh/id_ed25519\n")
        new_lines.append(f"    StrictHostKeyChecking accept-new\n")
    
    # Write back
    with open(SSH_CONFIG_PATH, 'w') as f:
        f.writelines(new_lines)
    
    print(f"✅ SSH config updated. You can now connect with: ssh {host_name}")


def setup_remote_environment(host_name: str, requirements_path: Optional[str] = None):
    """Setup Python environment on the remote pod."""
    print(f"🐍 Setting up Python environment on {host_name}...")
    
    commands = [
        # Create venv
        "python3 -m venv /tmp/venv",
        # Upgrade pip
        "/tmp/venv/bin/pip install --upgrade pip",
    ]
    
    # If requirements.txt provided, install it
    if requirements_path and Path(requirements_path).exists():
        print(f"📦 Installing requirements from {requirements_path}...")
        # Copy requirements file to remote
        subprocess.run(
            ["scp", requirements_path, f"{host_name}:/tmp/requirements.txt"],
            check=True
        )
        commands.append("/tmp/venv/bin/pip install -r /tmp/requirements.txt")
    
    # Execute commands
    for cmd in commands:
        print(f"  Running: {cmd}")
        result = subprocess.run(
            ["ssh", host_name, cmd],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"⚠️  Warning: Command failed: {result.stderr}")
        else:
            print(f"  ✓ Success")
    
    print("✅ Remote environment setup complete!")


def main():
    """Main entry point."""
    print("🎯 RunPod Setup Automation")
    print("=" * 50)
    
    # Get user input
    pod_name = input("Pod name (e.g., 'my-project'): ").strip()
    if not pod_name:
        print("❌ Pod name is required")
        sys.exit(1)
    
    # GPU configuration
    print("\nGPU Configuration:")
    print("1. 1x A100 (80GB)")
    print("2. 4x A100 (80GB)")
    print("3. Custom")
    
    choice = input("Choose (1-3) [default: 1]: ").strip() or "1"
    
    if choice == "1":
        gpu_count = 1
        gpu_display_name = "A100"
    elif choice == "2":
        gpu_count = 4
        gpu_display_name = "A100"
    else:
        gpu_count = int(input("GPU count: "))
        gpu_display_name = input("GPU display name (e.g., 'A100', 'A6000'): ")
    
    # Resolve GPU type to ID
    print(f"🔍 Looking up GPU type ID for '{gpu_display_name}'...")
    gpu_type_id = find_gpu_type_id(gpu_display_name)
    if not gpu_type_id:
        print(f"❌ Could not find GPU type matching '{gpu_display_name}'")
        print("Available GPU types:")
        for gpu in list_gpu_types()[:10]:  # Show first 10
            print(f"  - {gpu['displayName']} (ID: {gpu['id']})")
        sys.exit(1)
    print(f"✅ Found GPU type ID: {gpu_type_id}")
    
    disk_size = int(input("Disk size in GB [default: 200]: ").strip() or "200")
    
    volume_id = input("Network volume ID (optional, press Enter to skip): ").strip() or None
    
    # Ask about template vs image
    print("\nConfiguration:")
    print("1. Use a template name (recommended - faster startup)")
    print("2. Use a Docker image directly")
    config_choice = input("Choose (1-2) [default: 1]: ").strip() or "1"
    
    template_id = None
    image_name = None
    
    if config_choice == "1":
        # Use template - input the template name directly
        print("\nTemplate name (common templates: runpod-torch-v280, runpod-pytorch-v21, etc.)")
        template_name = input("Template name [default: runpod-torch-v280]: ").strip() or "runpod-torch-v280"
        
        # Try to look up the template
        print(f"🔍 Looking up template '{template_name}'...")
        template_id = find_template_by_name(template_name)
        
        if not template_id:
            # If not found, ask user for the ID directly
            print(f"   Could not find template '{template_name}' in your templates.")
            print("   You can find template names at: https://www.console.runpod.io/explore")
            use_anyway = input(f"   Use '{template_name}' as template ID anyway? (y/n) [y]: ").strip().lower()
            if use_anyway != 'n':
                template_id = template_name
                print(f"   Using '{template_name}' as template ID")
            else:
                print("   Falling back to Docker image")
                config_choice = "2"
    
    if config_choice == "2":
        # Use Docker image
        print("\nDocker image [default: runpod/pytorch]:")
        print("  Common options: runpod/pytorch, runpod/tensorflow, runpod/base")
        image_name = input("Image name: ").strip() or "runpod/pytorch"
    
    # Create the pod
    pod_id = create_pod(
        name=pod_name,
        gpu_type=gpu_type_id,
        gpu_count=gpu_count,
        volume_id=volume_id,
        disk_size=disk_size,
        image_name=image_name,
        template_id=template_id
    )
    
    if not pod_id:
        sys.exit(1)
    
    # Wait for pod to be ready
    connection_info = wait_for_pod_ready(pod_id)
    
    if not connection_info:
        sys.exit(1)
    
    # Update SSH config
    ssh_host = f"runpod-{pod_name}"
    update_ssh_config(
        host_name=ssh_host,
        ip=connection_info['ip'],
        port=connection_info['port']
    )
    
    # Setup remote environment
    setup_env = input("\nSetup Python environment? (y/n) [default: y]: ").strip().lower()
    if setup_env != 'n':
        requirements = input("Path to requirements.txt (optional, press Enter to skip): ").strip()
        try:
            setup_remote_environment(ssh_host, requirements or None)
        except Exception as e:
            print(f"⚠️  Warning: Could not setup remote environment: {e}")
            print("   You can do this manually later.")
    
    print("\n" + "=" * 50)
    print("🎉 Setup complete!")
    print(f"\n📌 Connection info:")
    print(f"   SSH host: {ssh_host}")
    print(f"   IP: {connection_info['ip']}")
    print(f"   Port: {connection_info['port']}")
    print(f"\n📌 Next steps:")
    print(f"   1. Test connection: ssh {ssh_host}")
    print(f"      (or: ssh -p {connection_info['port']} root@{connection_info['ip']})")
    print(f"   2. Open VS Code and connect to remote host")
    print(f"   3. Python venv is at: /tmp/venv")
    print(f"   4. Set interpreter to: /tmp/venv/bin/python")
    
    # Optional: Test SSH connection
    test_ssh = input("\n🔍 Test SSH connection now? (y/n) [n]: ").strip().lower()
    if test_ssh == 'y':
        print(f"Testing connection to {ssh_host}...")
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=10", ssh_host, "echo 'Connection successful!'"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ SSH connection works!")
        else:
            print(f"⚠️  SSH connection failed:")
            print(f"   {result.stderr}")
            print(f"\n   Try manually: ssh -p {connection_info['port']} root@{connection_info['ip']}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

