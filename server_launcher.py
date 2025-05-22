import subprocess

def is_server_running():
    result = subprocess.run(['pgrep', '-f', 'server.py'],stdout=subprocess.PIPE)
    return result.returncode == 0

def launch_server():
    if not is_server_running():
        print("Launching server.py...")
        subprocess.Popen(['nohup', 'python3', 'server.py', '&'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        print("Server already running")