# GitHub Actions CI/CD Setup Guide

This guide helps you configure GitHub Actions for automated deployment of the Agent 007 backend to AWS EC2.

## Prerequisites

1. AWS Account with free tier access
2. GitHub repository for this project
3. Google Gemini API key

## Required GitHub Secrets

Go to your repository → Settings → Secrets and variables → Actions

### AWS Configuration
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `AWS_REGION`: `us-east-1` (or preferred region)

### Application Configuration  
- `GOOGLE_API_KEY`: Your Google Gemini API key
- `BACKEND_PORT`: `8000`
- `ALLOWED_ORIGINS`: `https://your-frontend-domain.com,http://localhost:3000`
- `GEMINI_DEFAULT_MODEL`: `gemini-2.5-flash-lite`
- `GEMINI_HEAVY_MODEL`: `gemini-2.5-pro`
- `EMBEDDING_MODEL`: `gemini-embedding-001`

### EC2 Configuration (add after first deployment)
- `EC2_HOST`: IP address of your EC2 instance
- `EC2_USER`: `ubuntu`
- `EC2_PRIVATE_KEY`: SSH private key for EC2 access

## Initial Setup

1. **Generate SSH Key Pair**:
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/agent007-key
```

2. **Manual First Deployment**:
```bash
chmod +x scripts/deploy-ec2.sh
./scripts/deploy-ec2.sh
```

3. **Add EC2 secrets to GitHub** after deployment

## Monitoring

The CI/CD pipeline includes:
- Automated testing with pytest
- Docker security scanning
- Health checks after deployment
- Automatic rollback on failures

## Troubleshooting

- Check GitHub Actions logs for deployment issues
- Verify AWS credentials and permissions
- Ensure EC2 security groups allow SSH (port 22) and HTTP (port 8000)
- Monitor AWS free tier usage to avoid charges

## Manual Operations

### Health Check
```bash
curl http://your-ec2-ip:8000/health
```

### View Logs
```bash
ssh -i ~/.ssh/agent007-key ubuntu@your-ec2-ip
sudo docker logs agent007-backend
```

### Manual Rollback
```bash
sudo /opt/agent007/scripts/rollback.sh previous
```