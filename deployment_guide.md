# Deployment Guide

This guide covers both local deployment and deployment on AWS EC2.

## Local Deployment

### Prerequisites
1. Python 3.8 or higher
2. Ollama installed and running
3. Git (optional, for version control)

### Steps

1. **Set up Python environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Start Ollama**
```bash
ollama run llama2
```

3. **Start the FastAPI server**
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## AWS EC2 Deployment

### Prerequisites
1. AWS account
2. AWS CLI configured
3. Basic knowledge of EC2 and security groups

### Steps

1. **Launch EC2 Instance**
   - Go to AWS Console → EC2
   - Click "Launch Instance"
   - Choose Ubuntu Server 22.04 LTS
   - Select t2.large or better (recommended: t2.xlarge for better performance)
   - Configure storage: at least 20GB
   - Configure security group:
     - Allow SSH (port 22) from your IP
     - Allow HTTP (port 80) from anywhere
     - Allow custom TCP (port 8000) from anywhere
   - Launch instance and download key pair

2. **Connect to Instance**
```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@your-instance-ip
```

3. **Update System and Install Dependencies**
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git
```

4. **Install Ollama**
```bash
curl https://ollama.ai/install.sh | sh
```

5. **Clone Repository and Set Up Environment**
```bash
git clone <repository-url>
cd <repository-name>
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

6. **Start Ollama Service**
```bash
ollama run llama2
```

7. **Set Up Systemd Service for FastAPI**

Create a service file:
```bash
sudo nano /etc/systemd/system/llama-api.service
```

Add the following content:
```ini
[Unit]
Description=Llama 3 8B API Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/<repository-name>
Environment="PATH=/home/ubuntu/<repository-name>/venv/bin"
ExecStart=/home/ubuntu/<repository-name>/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable llama-api
sudo systemctl start llama-api
```

8. **Set Up Nginx (Optional but Recommended)**

Install Nginx:
```bash
sudo apt install -y nginx
```

Create Nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/llama-api
```

Add the following configuration:
```nginx
server {
    listen 80;
    server_name your-domain-or-ip;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable the site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/llama-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Monitoring and Maintenance

1. **Check Service Status**
```bash
sudo systemctl status llama-api
```

2. **View Logs**
```bash
sudo journalctl -u llama-api
```

3. **Monitor System Resources**
```bash
htop
```

4. **Backup and Updates**
- Regularly backup your model and configuration
- Keep the system and dependencies updated
- Monitor disk space usage

### Security Considerations

1. **Firewall Configuration**
```bash
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow 8000
sudo ufw enable
```

2. **SSL/TLS Setup (Recommended)**
- Use Let's Encrypt for free SSL certificates
- Configure Nginx to use HTTPS

3. **Regular Updates**
```bash
sudo apt update
sudo apt upgrade
```

### Troubleshooting

1. **Service Won't Start**
- Check logs: `sudo journalctl -u llama-api`
- Verify Ollama is running: `ollama list`
- Check port availability: `sudo netstat -tulpn | grep 8000`

2. **High Resource Usage**
- Monitor with `htop`
- Adjust EC2 instance size if needed
- Consider implementing rate limiting

3. **API Not Responding**
- Check service status
- Verify security group settings
- Check Nginx configuration if using

### Scaling Considerations

1. **Vertical Scaling**
- Increase EC2 instance size
- Add more memory/CPU

2. **Horizontal Scaling**
- Consider using AWS Elastic Load Balancer
- Implement multiple API instances
- Use shared cache (Redis/Memcached)

Remember to regularly monitor your AWS costs and adjust resources as needed. 