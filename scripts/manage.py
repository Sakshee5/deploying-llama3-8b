#!/usr/bin/env python3
import argparse
import subprocess
import os
import sys
import psutil
import json
from datetime import datetime

def run_command(command, shell=False):
    try:
        if shell:
            subprocess.run(command, shell=True, check=True)
        else:
            subprocess.run(command.split(), check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(f"Error: {str(e)}")
        sys.exit(1)

def start_service():
    print("Starting Llama API service...")
    if os.name == 'nt':  # Windows
        run_command("uvicorn app:app --host 0.0.0.0 --port 8000", shell=True)
    else:  # Unix/Linux
        run_command("sudo systemctl start llama-api")

def stop_service():
    print("Stopping Llama API service...")
    if os.name == 'nt':  # Windows
        # Find and kill the uvicorn process
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if 'uvicorn' in ' '.join(proc.info['cmdline'] or []):
                proc.kill()
    else:  # Unix/Linux
        run_command("sudo systemctl stop llama-api")

def restart_service():
    print("Restarting Llama API service...")
    stop_service()
    start_service()

def check_status():
    print("Checking service status...")
    if os.name == 'nt':  # Windows
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if 'uvicorn' in ' '.join(proc.info['cmdline'] or []):
                print("Service is running")
                return
        print("Service is not running")
    else:  # Unix/Linux
        run_command("sudo systemctl status llama-api")

def view_logs(lines=50):
    print(f"Viewing last {lines} lines of logs...")
    if os.name == 'nt':  # Windows
        if os.path.exists('api.log'):
            with open('api.log', 'r') as f:
                log_lines = f.readlines()
                print(''.join(log_lines[-lines:]))
        else:
            print("No log file found")
    else:  # Unix/Linux
        run_command(f"sudo journalctl -u llama-api -n {lines}")

def monitor_performance(duration=60):
    print(f"Monitoring performance for {duration} seconds...")
    metrics = []
    start_time = datetime.now()
    
    while (datetime.now() - start_time).seconds < duration:
        if os.name == 'nt':  # Windows
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
                if 'uvicorn' in ' '.join(proc.info['cmdline'] or []):
                    metrics.append({
                        'timestamp': datetime.now().isoformat(),
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_percent': proc.info['memory_percent']
                    })
        else:  # Unix/Linux
            # Get system metrics
            metrics.append({
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent
            })
        
        time.sleep(1)
    
    # Save metrics to file
    with open('performance_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Performance metrics saved to performance_metrics.json")

def main():
    parser = argparse.ArgumentParser(description='Manage Llama API Service')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'logs', 'monitor'],
                      help='Action to perform')
    parser.add_argument('--lines', type=int, default=50,
                      help='Number of log lines to display (for logs action)')
    parser.add_argument('--duration', type=int, default=60,
                      help='Duration of performance monitoring in seconds (for monitor action)')
    
    args = parser.parse_args()
    
    if args.action == 'start':
        start_service()
    elif args.action == 'stop':
        stop_service()
    elif args.action == 'restart':
        restart_service()
    elif args.action == 'status':
        check_status()
    elif args.action == 'logs':
        view_logs(args.lines)
    elif args.action == 'monitor':
        monitor_performance(args.duration)

if __name__ == '__main__':
    main() 