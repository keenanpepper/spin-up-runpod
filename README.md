# RunPod Setup Automation

A simple Python script to automate the creation and setup of RunPod instances.

## What it automates

✅ **Fully Automated:**
- Creates RunPod instance via API
- Waits for pod to be ready
- Updates your SSH config automatically
- Connects and creates Python venv
- Installs requirements.txt (optional)

⚠️ **Manual steps** (you still do these):
- Open VS Code and connect to remote host
- Install Python extension in remote environment
- Select interpreter (/tmp/venv/bin/python)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file with your RunPod API key:
```bash
cp .env.example .env
# Edit .env and add your RUNPOD_API_KEY
```

## Usage

Simply run:
```bash
python setup_runpod.py
```

The script will:
1. Ask for pod name (e.g., "my-project")
2. Ask for GPU configuration (defaults to 1x A100)
3. Ask for disk size (defaults to 200GB)
4. Create the pod and wait for it to be ready
5. Update your SSH config at `~/.ssh/config`
6. Setup Python environment remotely

After the script completes, you can:
- Connect via SSH: `ssh runpod-<your-pod-name>`
- Open VS Code and connect to the remote host
- The Python venv is ready at `/tmp/venv`

## Configuration

The script uses sensible defaults:
- **GPU options**: 1x A100 or 4x A100 (or custom)
- **Disk size**: 200GB (configurable)
- **Python venv**: `/tmp/venv`
- **SSH config**: Automatically updated with `StrictHostKeyChecking accept-new`

## Example

```bash
$ python setup_runpod.py

🎯 RunPod Setup Automation
==================================================
Pod name (e.g., 'my-project'): esr-training

GPU Configuration:
1. 1x A100 (80GB)
2. 4x A100 (80GB)
3. Custom
Choose (1-3) [default: 1]: 1

Disk size in GB [default: 200]: 300
Network volume ID (optional, press Enter to skip): 

🚀 Creating pod 'esr-training' with 1x NVIDIA A100 80GB PCIe...
✅ Pod created with ID: abc123xyz
⏳ Waiting for pod to be ready.....
✅ Pod is ready!
📝 Updating SSH config for host 'runpod-esr-training'...
✅ SSH config updated. You can now connect with: ssh runpod-esr-training

Setup Python environment? (y/n) [default: y]: y
Path to requirements.txt (optional, press Enter to skip): ./my-project/requirements.txt
🐍 Setting up Python environment on runpod-esr-training...
📦 Installing requirements from ./my-project/requirements.txt...
  Running: python3 -m venv /tmp/venv
  ✓ Success
  Running: /tmp/venv/bin/pip install --upgrade pip
  ✓ Success
  Running: /tmp/venv/bin/pip install -r /tmp/requirements.txt
  ✓ Success
✅ Remote environment setup complete!

==================================================
🎉 Setup complete!

📌 Next steps:
   1. Connect with: ssh runpod-esr-training
   2. Open VS Code and connect to remote host
   3. Python venv is at: /tmp/venv
   4. Set interpreter to: /tmp/venv/bin/python
```

## Notes

- The script adds `StrictHostKeyChecking accept-new` to your SSH config to automatically accept new host fingerprints
- If a host with the same name exists in your SSH config, it will be updated with the new connection info
- The venv is created in `/tmp/venv` (adjust in the script if you prefer a different location)

