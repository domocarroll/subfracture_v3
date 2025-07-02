#!/bin/bash

# 🌊 SUBFRACTURE DigitalOcean Deployment Script
# Automates the complete deployment process

set -e  # Exit on any error

echo "🌊 SUBFRACTURE DigitalOcean Deployment"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v doctl &> /dev/null; then
        log_error "doctl CLI not found. Please install: https://docs.digitalocean.com/reference/doctl/how-to/install/"
        exit 1
    fi
    
    if ! command -v git &> /dev/null; then
        log_error "git not found. Please install git."
        exit 1
    fi
    
    # Check if authenticated with DigitalOcean
    if ! doctl account get &> /dev/null; then
        log_error "Not authenticated with DigitalOcean. Run: doctl auth init"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create managed databases
create_databases() {
    log_info "Creating managed databases..."
    
    # Check if PostgreSQL cluster exists
    if doctl databases get subfracture-db &> /dev/null; then
        log_warning "PostgreSQL cluster 'subfracture-db' already exists"
    else
        log_info "Creating PostgreSQL cluster..."
        doctl databases create subfracture-db \
            --engine postgres \
            --version 15 \
            --region nyc1 \
            --size db-s-1vcpu-1gb \
            --num-nodes 1
        log_success "PostgreSQL cluster created"
    fi
    
    # Check if Redis cluster exists
    if doctl databases get subfracture-cache &> /dev/null; then
        log_warning "Redis cluster 'subfracture-cache' already exists"
    else
        log_info "Creating Redis cluster..."
        doctl databases create subfracture-cache \
            --engine redis \
            --version 7 \
            --region nyc1 \
            --size db-s-1vcpu-1gb
        log_success "Redis cluster created"
    fi
}

# Deploy application
deploy_app() {
    log_info "Deploying SUBFRACTURE application..."
    
    if [ ! -f ".do/app.yaml" ]; then
        log_error "DigitalOcean app spec not found. Make sure .do/app.yaml exists."
        exit 1
    fi
    
    # Check if app already exists
    APP_NAME="subfracture-production"
    if doctl apps list --format Name --no-header | grep -q "^${APP_NAME}$"; then
        log_warning "App '${APP_NAME}' already exists. Updating..."
        APP_ID=$(doctl apps list --format ID,Name --no-header | grep "${APP_NAME}" | cut -d' ' -f1)
        doctl apps update $APP_ID --spec .do/app.yaml
    else
        log_info "Creating new app..."
        doctl apps create --spec .do/app.yaml
        APP_ID=$(doctl apps list --format ID,Name --no-header | grep "${APP_NAME}" | cut -d' ' -f1)
    fi
    
    log_success "Application deployment initiated. App ID: $APP_ID"
}

# Wait for deployment
wait_for_deployment() {
    log_info "Waiting for deployment to complete..."
    
    local app_id=$1
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        status=$(doctl apps get $app_id --format Phase --no-header)
        
        case $status in
            "ACTIVE")
                log_success "Deployment completed successfully!"
                return 0
                ;;
            "BUILDING"|"DEPLOYING")
                log_info "Deployment in progress... ($status)"
                ;;
            "ERROR"|"FAILED")
                log_error "Deployment failed!"
                doctl apps logs $app_id --component server --tail 50
                return 1
                ;;
        esac
        
        sleep 30
        ((attempt++))
    done
    
    log_warning "Deployment taking longer than expected. Check manually."
    return 1
}

# Get connection info
get_connection_info() {
    log_info "Getting connection information..."
    
    # Get app URL
    APP_ID=$(doctl apps list --format ID,Name --no-header | grep "subfracture-production" | cut -d' ' -f1)
    APP_URL=$(doctl apps get $APP_ID --format LiveURL --no-header)
    
    # Get database connection strings
    POSTGRES_URI=$(doctl databases connection subfracture-db --format URI --no-header)
    REDIS_URI=$(doctl databases connection subfracture-cache --format PrivateURI --no-header)
    
    echo ""
    log_success "🎉 Deployment Complete!"
    echo "=================================="
    echo ""
    echo "🌐 Application URL: $APP_URL"
    echo "🗄️  PostgreSQL URI: $POSTGRES_URI"
    echo "🔴 Redis URI: $REDIS_URI"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Visit $APP_URL to test your application"
    echo "2. Configure your custom domain if needed"
    echo "3. Set up monitoring and alerts"
    echo ""
    echo "🔧 Useful Commands:"
    echo "   View logs: doctl apps logs $APP_ID --component server --follow"
    echo "   App status: doctl apps get $APP_ID"
    echo "   Scale app: doctl apps update $APP_ID --spec .do/app.yaml"
    echo ""
}

# Health check
health_check() {
    local app_url=$1
    log_info "Performing health check..."
    
    if curl -f -s "${app_url}/health" > /dev/null; then
        log_success "Health check passed!"
    else
        log_warning "Health check failed. Check application logs."
    fi
}

# Main deployment flow
main() {
    echo ""
    log_info "Starting SUBFRACTURE deployment to DigitalOcean..."
    echo ""
    
    check_prerequisites
    echo ""
    
    create_databases
    echo ""
    
    deploy_app
    echo ""
    
    # Get app ID for monitoring
    APP_ID=$(doctl apps list --format ID,Name --no-header | grep "subfracture-production" | cut -d' ' -f1)
    
    if wait_for_deployment $APP_ID; then
        get_connection_info
        
        # Get app URL for health check
        APP_URL=$(doctl apps get $APP_ID --format LiveURL --no-header)
        health_check $APP_URL
    else
        log_error "Deployment failed or timed out."
        exit 1
    fi
}

# Run main function
main "$@"