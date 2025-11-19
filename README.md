# RunPod Automation

Automate the entire process of creating and setting up a new RunPod instance, from API calls to environment configuration.

## Features

✅ Creates RunPod instance via API with your specs  
✅ Automatically configures SSH keys  
✅ Updates your `~/.ssh/config` for easy access  
✅ Waits for pod to be ready  
✅ Creates Python virtual environment  
✅ Installs your project dependencies  
✅ Generates VS Code settings template  

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Your Pod

Create a YAML config file (or use `selfie_pod.yaml` as a template):

```yaml
disk_space_gb: 200
gpu_type: NVIDIA A100 80GB PCIe  # Use exact GPU type ID
num_gpus: 1
network_volume_id: wup549p1f2
pod_name: Keenan-MyProject
requirements_file: /workspace/my-project/requirements.txt
template_id: runpod-torch-v280
venv_path: /tmp/venv
vscode_extensions:
  - ms-python.python
```

### 3. Set Up Environment

Make sure you have a `.env` file with your RunPod API key:

```bash
RUNPOD_API_KEY=your_api_key_here
```

### 4. Run the Automation

```bash
python setup_runpod.py selfie_pod.yaml
```

Or if you made it executable:

```bash
./setup_runpod.py selfie_pod.yaml
```

## What It Does

### Phase 1: Pod Creation
- Queries your RunPod account for SSH public keys
- Automatically detects the datacenter from your network volume location
- Creates a pod with your specified GPU type, count, and network volume
- Uses the template to pre-configure the environment
- **Critically**: Adds your SSH keys as environment variable (required for SSH access via API)

### Phase 2: SSH Configuration
- Waits for the pod to start and get an IP address
- Automatically updates `~/.ssh/config` with the new connection details
- Sets `StrictHostKeyChecking=accept-new` to auto-accept fingerprints

### Phase 3: Environment Setup
- Waits for SSH to become available
- Creates a Python virtual environment at the specified path
- Upgrades pip
- Installs your project requirements

### Phase 4: VS Code Integration
- **Automatically installs VS Code extensions** specified in your config
- Creates a `.vscode/settings.json.template` with the correct Python interpreter path
- If no extensions are specified, this step is skipped

## Configuration Fields

| Field | Description | Example |
|-------|-------------|---------|
| `disk_space_gb` | Disk space (reference only, template controls this) | `200` |
| `gpu_type` | **Exact** GPU type ID from RunPod | `NVIDIA A100 80GB PCIe` |
| `num_gpus` | Number of GPUs | `1` |
| `network_volume_id` | Your network volume ID | `wup549p1f2` |
| `pod_name` | Name for the pod and SSH config entry (spaces → dashes for SSH) | `Keenan-MyProject` |
| `requirements_file` | Path to requirements.txt on the remote | `/workspace/project/requirements.txt` |
| `template_id` | RunPod template ID | `runpod-torch-v280` |
| `venv_path` | Where to create the venv | `/tmp/venv` |
| `vscode_extensions` | **(Optional)** List of extension IDs to install | `["ms-python.python"]` |

**Notes**:
- The datacenter is automatically detected from your network volume's location
- If your `pod_name` contains spaces, they'll be replaced with dashes for the SSH config host name (e.g., "My Pod" → "My-Pod")

## After Setup

Once the script completes, you can:

### Connect via SSH
```bash
ssh <pod_name>
```

### Open in VS Code
```bash
code --remote ssh-remote+<pod_name> /workspace
```

The Python extension is already installed and ready to use!

### Set Python Interpreter (Optional)
1. Open Command Palette (⌘⇧P)
2. Type "Python: Select Interpreter"
3. Choose `/tmp/venv/bin/python` (or your configured venv_path)

Or copy the generated `.vscode/settings.json.template` to your workspace's `.vscode/settings.json`.

## Discovery Tools

Before creating a pod, you can use these utilities to find the right configuration:

### List Available GPUs
```bash
python list_gpus.py
```
Shows all GPU types with their **exact IDs** (required for config).

### List Datacenters
```bash
python list_datacenters.py
```
Shows your network volumes and their datacenter locations.

## Troubleshooting

### GPU Type Not Available
**Problem**: "There are no longer any instances available with the requested specifications"

**Solutions**:
1. **Use exact GPU type ID**: Run `python list_gpus.py` to get the precise ID
   - ❌ Bad: `A100`
   - ✅ Good: `NVIDIA A100 80GB PCIe`
2. **Specify datacenter**: Add `datacenter_id` to your config to target specific region
   - Run `python list_datacenters.py` to see where your network volume is located
3. **Try different GPU**: Check RunPod web UI for current availability
4. **Wait and retry**: Availability changes frequently

### SSH Not Working
- Wait a bit longer - pods can take time to fully boot
- Check the pod is running in RunPod web UI
- Verify your SSH key is in your RunPod account settings

### Requirements Installation Failed
- Make sure `requirements_file` path is correct (should be on the remote pod)
- The path should point to your network volume: `/workspace/<your-project>/requirements.txt`

## Advanced Usage

### Multiple Configs
Create different YAML files for different projects:

```bash
./setup_runpod.py project1.yaml
./setup_runpod.py project2.yaml
```

### Custom VS Code Extensions

Specify which extensions to install by adding them to your config:

```yaml
vscode_extensions:
  - ms-python.python
  - ms-python.vscode-pylance
  - ms-toolsai.jupyter
  - github.copilot
```

If you don't want any extensions installed, simply omit this field or use an empty list:

```yaml
vscode_extensions: []
```

**Note**: The `code` CLI must be available in your PATH for extension installation to work. If it's not found, the script will skip this step and continue.

### Custom Setup Commands
Edit the `setup_remote_environment()` function to add custom setup steps like:
- Installing system packages
- Cloning repositories
- Setting up environment variables
- Running initialization scripts

## Managing Your Pods

Use the included `manage_pods.py` utility to view and manage your existing pods:

```bash
# List all your pods
python manage_pods.py list

# Get detailed info about a specific pod
python manage_pods.py details <pod_id>

# Stop a pod (but keep it for later)
python manage_pods.py stop <pod_id>

# Terminate (delete) a pod permanently
python manage_pods.py terminate <pod_id>
```

This is helpful for:
- Checking which pods are running and their costs
- Finding SSH connection details
- Cleaning up old pods to save money

## See Also

- `FINDINGS.md` - Important notes about RunPod API quirks
- RunPod API docs: https://graphql-spec.runpod.io/

