# 🌊 SUBFRACTURE DigitalOcean Deployment Guide

## Quick Deployment Steps

### 1. Create DigitalOcean Account & Setup
1. Sign up at [DigitalOcean](https://digitalocean.com)
2. Install `doctl` CLI: `snap install doctl` or `brew install doctl`
3. Authenticate: `doctl auth init`

### 2. Deploy via App Platform (Recommended)

#### Option A: Web Interface
1. Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Click "Create App"
3. Connect GitHub repository: `domocarroll/subfracture_v3`
4. Select branch: `main`
5. Import the `.do/app.yaml` configuration
6. Deploy!

#### Option B: CLI Deployment
```bash
# Clone repository
git clone https://github.com/domocarroll/subfracture_v3.git
cd subfracture_v3

# Deploy to DigitalOcean
doctl apps create --spec .do/app.yaml

# Check deployment status
doctl apps list
doctl apps get <app-id>
```

### 3. Configure Managed Databases

#### PostgreSQL Database
```bash
# Create managed PostgreSQL cluster
doctl databases create subfracture-db --engine postgres --version 15 --region nyc1 --size db-s-1vcpu-1gb

# Get connection details
doctl databases connection subfracture-db --format "Host,Port,User,Password,Database,URI"
```

#### Redis Cache
```bash
# Create managed Redis cluster  
doctl databases create subfracture-cache --engine redis --version 7 --region nyc1 --size db-s-1vcpu-1gb

# Get connection details
doctl databases connection subfracture-cache --format "Host,Port,Password,URI"
```

### 4. Environment Variables Setup

Add these to your DigitalOcean App Platform environment variables:

#### Server Environment Variables
```bash
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://user:pass@host:port
METRICS_PORT=8000
MCP_PORT=8001
PYTHONPATH=/app
```

#### Client Environment Variables  
```bash
VITE_MCP_SERVER_URL=wss://your-app.ondigitalocean.app
VITE_AG_UI_SERVER_URL=https://your-app.ondigitalocean.app
VITE_ENVIRONMENT=production
```

## Alternative: Docker Container Deployment

### 1. Build and Push to Container Registry
```bash
# Build and tag
docker build -t registry.digitalocean.com/your-registry/subfracture-server:latest ./server
docker build -t registry.digitalocean.com/your-registry/subfracture-client:latest ./client

# Push to DO Container Registry
docker push registry.digitalocean.com/your-registry/subfracture-server:latest
docker push registry.digitalocean.com/your-registry/subfracture-client:latest
```

### 2. Deploy with Droplets
```bash
# Create Droplet
doctl compute droplet create subfracture-prod \
    --size s-2vcpu-4gb \
    --image docker-20-04 \
    --region nyc1 \
    --ssh-keys your-ssh-key-id

# SSH and deploy
ssh root@your-droplet-ip
git clone https://github.com/domocarroll/subfracture_v3.git
cd subfracture_v3
docker-compose -f docker-compose.digitalocean.yml up -d
```

## Database Initialization

### PostgreSQL Schema Setup
```bash
# Connect to managed database
psql $DATABASE_URL

# Run migrations
\i database/schema.sql
```

### Redis Configuration
```bash
# Redis typically requires no setup for this use case
# Connection will be handled automatically by the application
```

## Monitoring & Logging

### Application Metrics
- **Prometheus metrics**: Available at `https://your-app.ondigitalocean.app:8000/metrics`
- **Health check**: `https://your-app.ondigitalocean.app/health`

### DigitalOcean Monitoring
```bash
# Enable monitoring
doctl monitoring alert policy create \
    --name "SUBFRACTURE Health Check" \
    --type v1/insights/droplet/load_5 \
    --compare greater_than \
    --value 0.8 \
    --window 5m \
    --entities droplet:your-droplet-id
```

## Domain & SSL Setup

### Custom Domain
1. Add domain in DigitalOcean App Platform settings
2. Update DNS records to point to DigitalOcean
3. SSL certificates are automatically managed

### DNS Configuration
```
A record: @ -> your-app-ip
CNAME record: www -> your-app.ondigitalocean.app
```

## Performance Optimization

### App Platform Scaling
```bash
# Scale server instances
doctl apps update <app-id> --spec .do/app.yaml

# Monitor performance
doctl apps logs <app-id> --component server --follow
```

### Database Performance
- **Connection pooling**: Configured in FastMCP server
- **Query optimization**: Built into SQLAlchemy models
- **Caching**: Redis for session data and temporary storage

## Security Considerations

### Network Security
- All services communicate over private network
- Database access restricted to application
- SSL/TLS encryption for all external connections

### Application Security
- Input validation with Pydantic
- SQL injection protection via SQLAlchemy
- Rate limiting on API endpoints
- Error boundary protection

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```bash
# Check database status
doctl databases get subfracture-db

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

#### 2. FastMCP Server Not Starting
```bash
# Check logs
doctl apps logs <app-id> --component server --tail 100

# Common fixes:
# - Verify all environment variables are set
# - Check database connectivity
# - Ensure port 8001 is not blocked
```

#### 3. Frontend Not Loading
```bash
# Check build logs
doctl apps logs <app-id> --component client --tail 100

# Verify environment variables:
# - VITE_MCP_SERVER_URL should use wss:// protocol
# - Domain should match your actual deployment URL
```

## Cost Optimization

### Recommended Resources
- **Server**: Professional XS ($12/month)
- **Client**: Basic XXS ($5/month) 
- **PostgreSQL**: Basic ($15/month)
- **Redis**: Basic ($15/month)
- **Total**: ~$47/month

### Scaling Strategy
- Start with basic resources
- Monitor performance metrics
- Scale up based on actual usage
- Use alerts to track resource utilization

## Backup & Recovery

### Database Backups
```bash
# Automated backups are enabled by default
# Manual backup
doctl databases backup subfracture-db

# Restore from backup
doctl databases restore subfracture-db --backup-id <backup-id>
```

### Application Backups
- Code is backed up via GitHub
- Configuration is version controlled
- Database migrations are tracked

## Support & Maintenance

### Health Monitoring
- **Uptime monitoring**: Built into DigitalOcean App Platform
- **Performance alerts**: Configured via doctl monitoring
- **Error tracking**: Sentry integration for production errors

### Updates & Deployment
```bash
# Deploy new version
git push origin main  # Triggers automatic deployment

# Manual deployment
doctl apps deploy <app-id>

# Rollback if needed
doctl apps rollback <app-id> --deployment-id <previous-deployment-id>
```

---

## 🎉 Success Criteria

Your SUBFRACTURE deployment is successful when:

✅ **FastMCP server** responds at `/health` endpoint  
✅ **All 15 brand intelligence tools** are working  
✅ **3D visualization** loads without errors  
✅ **Real-time collaboration** connects via WebSocket  
✅ **Database** migrations complete successfully  
✅ **Frontend** loads and connects to backend  

**Expected total deployment time: 15-30 minutes**

---

**Need help?** Check the troubleshooting section or create an issue in the repository.