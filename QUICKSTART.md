# Quick Start Guide

## 🎯 One-Command Setup

```bash
./setup_runpod.py selfie_pod.yaml
```

That's it! This single command will:
1. ✅ Create your RunPod with the right specs
2. ✅ Set up SSH access automatically
3. ✅ Create a Python virtual environment
4. ✅ Install your dependencies
5. ✅ Configure everything for VS Code

## Prerequisites

1. **Install dependencies** (one time):
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your API key** (in `.env`):
   ```
   RUNPOD_API_KEY=your_key_here
   ```

3. **Find your GPU type** (important - must be exact!):
   ```bash
   python list_gpus.py
   ```

4. **Configure your pod** (edit `selfie_pod.yaml` or create a new config):
   ```yaml
   disk_space_gb: 200
   gpu_type: NVIDIA A100 80GB PCIe  # Must be exact ID!
   num_gpus: 1
   network_volume_id: wup549p1f2
   pod_name: Keenan-MyProject
   requirements_file: /workspace/my-project/requirements.txt
   template_id: runpod-torch-v280
   venv_path: /tmp/venv
   vscode_extensions:
     - ms-python.python
   ```

   **Note**: Datacenter is automatically detected from your network volume!

## What Gets Automated

### ✅ Fully Automated
- Starting RunPod with your specs *(was: manual web UI)*
- SSH config updates *(was: copy-paste IP/port)*
- Accepting SSH fingerprint *(was: manual prompt)*
- Creating Python venv *(was: manual terminal command)*
- Installing requirements *(was: manual pip install)*
- **Installing VS Code extensions** *(was: manual VS Code UI)*

### 📝 Still Manual (But Easy)
1. Open VS Code: `code --remote ssh-remote+<pod_name> /workspace`
2. Start coding! Everything is already set up.

## Usage Examples

### Create a New Pod
```bash
# Using the default config
./setup_runpod.py selfie_pod.yaml

# Or create a custom config
./setup_runpod.py my_project.yaml
```

### Connect to Your Pod
After setup completes:
```bash
# SSH
ssh <pod_name>

# VS Code
code --remote ssh-remote+<pod_name> /workspace
```

### Manage Your Pods
```bash
# See all your pods
./manage_pods.py list

# Check details and cost
./manage_pods.py details <pod_id>

# Clean up when done
./manage_pods.py terminate <pod_id>
```

## Time Savings

**Before**: ~10-15 minutes of manual steps  
**After**: ~3-5 minutes (mostly waiting for pod to start)  
**Your effort**: Run one command, then just open VS Code!

**Manual steps reduced from 11 to 1** 🎉

## Typical Workflow

1. Edit your YAML config if needed (different GPU, project, etc.)
2. Run: `./setup_runpod.py my_config.yaml`
3. Wait ~2-3 minutes while it sets everything up
4. Open VS Code: `code --remote ssh-remote+<pod_name> /workspace`
5. Start coding immediately! 🚀

## Tips

- **Multiple projects**: Create different YAML configs for each project
- **Check costs**: Use `./manage_pods.py list` to see running pods and costs
- **Reuse configs**: Once you have a config that works, just reuse it
- **Network volumes**: Your data persists on the network volume between pods

## Troubleshooting

**"GPU not available" or "no instances available"**
- **Use exact GPU ID**: Run `python list_gpus.py` and copy the exact ID
  - ❌ Wrong: `A100`
  - ✅ Right: `NVIDIA A100 80GB PCIe`
- **Check datacenter**: Script automatically uses your network volume's datacenter
  - Run `python list_datacenters.py` to verify your volume's location
- Try a different GPU type or check RunPod web UI

**"SSH not working"**
- Wait 30-60 seconds more - pods take time to fully boot
- Check pod is running: `./manage_pods.py list`

**"Requirements not found"**
- Make sure `requirements_file` path points to your network volume
- Path should be like `/workspace/your-project/requirements.txt`

## Next Steps

See `README.md` for full documentation and advanced options.

