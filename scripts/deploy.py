#!/usr/bin/env python3
import argparse
import subprocess
import os
import sys
import boto3
import time
from pathlib import Path

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

def setup_local_environment():
    print("Setting up local environment...")
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists("venv"):
        run_command("python -m venv venv")
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        run_command("venv\\Scripts\\pip install -r requirements.txt")
    else:  # Unix/Linux
        run_command("source venv/bin/activate && pip install -r requirements.txt", shell=True)
    
    print("Local environment setup complete!")

def create_ec2_instance(instance_type, key_name):
    print("Creating EC2 instance...")
    
    ec2 = boto3.client('ec2')
    
    # Create security group
    security_group = ec2.create_security_group(
        GroupName='llama-api-sg',
        Description='Security group for Llama API'
    )
    
    # Configure security group
    ec2.authorize_security_group_ingress(
        GroupId=security_group['GroupId'],
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 22,
                'ToPort': 22,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            },
            {
                'IpProtocol': 'tcp',
                'FromPort': 80,
                'ToPort': 80,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            },
            {
                'IpProtocol': 'tcp',
                'FromPort': 8000,
                'ToPort': 8000,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }
        ]
    )
    
    # Launch EC2 instance
    response = ec2.run_instances(
        ImageId='ami-0c7217cdde317cfec',  # Ubuntu 22.04 LTS
        InstanceType=instance_type,
        MinCount=1,
        MaxCount=1,
        KeyName=key_name,
        SecurityGroupIds=[security_group['GroupId']],
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': 'llama-api-server'
                    }
                ]
            }
        ]
    )
    
    instance_id = response['Instances'][0]['InstanceId']
    print(f"EC2 instance created with ID: {instance_id}")
    
    # Wait for instance to be running
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    
    # Get instance public IP
    instance = ec2.describe_instances(InstanceIds=[instance_id])
    public_ip = instance['Reservations'][0]['Instances'][0]['PublicIpAddress']
    
    return instance_id, public_ip, security_group['GroupId']

def setup_ec2_instance(public_ip, key_path):
    print(f"Setting up EC2 instance at {public_ip}...")
    
    # Create deployment script
    deploy_script = """#!/bin/bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git nginx

# Install Ollama
curl https://ollama.ai/install.sh | sh

# Clone repository
git clone https://github.com/yourusername/llama-api.git
cd llama-api

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up Nginx
sudo tee /etc/nginx/sites-available/llama-api << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/llama-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Set up systemd service
sudo tee /etc/systemd/system/llama-api.service << EOF
[Unit]
Description=Llama 3 8B API Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/llama-api
Environment="PATH=/home/ubuntu/llama-api/venv/bin"
ExecStart=/home/ubuntu/llama-api/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable llama-api
sudo systemctl start llama-api
"""
    
    # Save deployment script
    with open('ec2_setup.sh', 'w') as f:
        f.write(deploy_script)
    
    # Copy deployment script to EC2
    run_command(f"scp -i {key_path} ec2_setup.sh ubuntu@{public_ip}:~")
    
    # Execute deployment script
    run_command(f"ssh -i {key_path} ubuntu@{public_ip} 'chmod +x ec2_setup.sh && ./ec2_setup.sh'")
    
    # Clean up
    os.remove('ec2_setup.sh')
    
    print("EC2 instance setup complete!")

def main():
    parser = argparse.ArgumentParser(description='Deploy Llama API')
    parser.add_argument('--mode', choices=['local', 'ec2'], required=True, help='Deployment mode')
    parser.add_argument('--instance-type', default='t2.large', help='EC2 instance type')
    parser.add_argument('--key-name', help='EC2 key pair name')
    parser.add_argument('--key-path', help='Path to EC2 private key file')
    
    args = parser.parse_args()
    
    if args.mode == 'local':
        setup_local_environment()
    elif args.mode == 'ec2':
        if not args.key_name or not args.key_path:
            print("Error: --key-name and --key-path are required for EC2 deployment")
            sys.exit(1)
        
        instance_id, public_ip, security_group_id = create_ec2_instance(args.instance_type, args.key_name)
        setup_ec2_instance(public_ip, args.key_path)
        
        print(f"\nDeployment complete!")
        print(f"Instance ID: {instance_id}")
        print(f"Public IP: {public_ip}")
        print(f"Security Group ID: {security_group_id}")
        print(f"\nAPI will be available at: http://{public_ip}")

if __name__ == '__main__':
    main() 