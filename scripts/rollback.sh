#!/bin/bash

# Rollback Script for Agent 007 Backend

set -euo pipefail

# Configuration
BACKUP_DIR="/opt/agent007/backups"
SERVICE_NAME="agent007-backend"
DOCKER_IMAGE_PREFIX="agent007-backend"
ROLLBACK_TARGET=${1:-"previous"}

# Logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ROLLBACK] $*"
}

# Check if running as root or with sudo
check_permissions() {
    if [[ $EUID -ne 0 ]]; then
        log "ERROR: This script must be run as root or with sudo"
        exit 1
    fi
}

# List available backups
list_backups() {
    log "Available backups:"
    if [[ -d "$BACKUP_DIR" ]]; then
        ls -la "$BACKUP_DIR"/ | grep -E "^d" | tail -n +2
    else
        log "No backups directory found at $BACKUP_DIR"
        exit 1
    fi
}

# Get the target backup directory
get_backup_target() {
    local target=$1
    
    if [[ "$target" == "list" ]]; then
        list_backups
        exit 0
    fi
    
    if [[ "$target" == "previous" ]]; then
        # Get the most recent backup
        target=$(ls -t "$BACKUP_DIR"/ | head -n 1)
        if [[ -z "$target" ]]; then
            log "ERROR: No backups found"
            exit 1
        fi
    fi
    
    local backup_path="$BACKUP_DIR/$target"
    if [[ ! -d "$backup_path" ]]; then
        log "ERROR: Backup not found: $backup_path"
        exit 1
    fi
    
    echo "$backup_path"
}

# Stop current service
stop_service() {
    log "Stopping current service..."
    
    # Stop Docker container
    if docker ps --filter "name=$SERVICE_NAME" --quiet | grep -q .; then
        docker stop "$SERVICE_NAME" || true
        docker rm "$SERVICE_NAME" || true
        log "Docker container stopped and removed"
    fi
    
    # Stop systemd service
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        systemctl stop "$SERVICE_NAME"
        log "Systemd service stopped"
    fi
}

# Backup current state before rollback
backup_current_state() {
    local backup_name="pre-rollback-$(date +%Y%m%d-%H%M%S)"
    local current_backup_dir="$BACKUP_DIR/$backup_name"
    
    log "Creating backup of current state: $backup_name"
    
    mkdir -p "$current_backup_dir"
    
    # Backup application files
    if [[ -d "/opt/agent007/current" ]]; then
        cp -r /opt/agent007/current "$current_backup_dir/app"
    fi
    
    # Backup configuration
    if [[ -f "/etc/systemd/system/$SERVICE_NAME.service" ]]; then
        cp "/etc/systemd/system/$SERVICE_NAME.service" "$current_backup_dir/"
    fi
    
    # Backup Docker image if exists
    if docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "$DOCKER_IMAGE_PREFIX"; then
        local current_image=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "$DOCKER_IMAGE_PREFIX" | head -n 1)
        docker save "$current_image" > "$current_backup_dir/docker-image.tar"
        echo "$current_image" > "$current_backup_dir/docker-image-name.txt"
    fi
    
    # Backup database/vector store
    if [[ -d "/opt/agent007/current/chroma_db" ]]; then
        cp -r /opt/agent007/current/chroma_db "$current_backup_dir/"
    fi
    
    log "Current state backed up to: $current_backup_dir"
}

# Restore from backup
restore_from_backup() {
    local backup_path=$1
    
    log "Restoring from backup: $backup_path"
    
    # Restore application files
    if [[ -d "$backup_path/app" ]]; then
        rm -rf /opt/agent007/current
        cp -r "$backup_path/app" /opt/agent007/current
        log "Application files restored"
    fi
    
    # Restore systemd service
    if [[ -f "$backup_path/$SERVICE_NAME.service" ]]; then
        cp "$backup_path/$SERVICE_NAME.service" "/etc/systemd/system/"
        systemctl daemon-reload
        log "Systemd service restored"
    fi
    
    # Restore Docker image
    if [[ -f "$backup_path/docker-image.tar" && -f "$backup_path/docker-image-name.txt" ]]; then
        docker load < "$backup_path/docker-image.tar"
        local image_name=$(cat "$backup_path/docker-image-name.txt")
        log "Docker image restored: $image_name"
    fi
    
    # Restore database/vector store
    if [[ -d "$backup_path/chroma_db" && -d "/opt/agent007/current" ]]; then
        rm -rf /opt/agent007/current/chroma_db
        cp -r "$backup_path/chroma_db" /opt/agent007/current/
        log "Database/vector store restored"
    fi
}

# Start service
start_service() {
    log "Starting service..."
    
    # Try Docker first if image exists
    if docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "$DOCKER_IMAGE_PREFIX"; then
        local image_name=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "$DOCKER_IMAGE_PREFIX" | head -n 1)
        
        docker run -d \
            --name "$SERVICE_NAME" \
            --restart unless-stopped \
            -p 8000:8000 \
            -v /opt/agent007/current:/app \
            -v /opt/agent007/current/chroma_db:/app/chroma_db \
            --env-file /opt/agent007/current/.env.production \
            "$image_name"
        
        log "Docker container started"
        return 0
    fi
    
    # Try systemd service
    if [[ -f "/etc/systemd/system/$SERVICE_NAME.service" ]]; then
        systemctl enable "$SERVICE_NAME"
        systemctl start "$SERVICE_NAME"
        log "Systemd service started"
        return 0
    fi
    
    log "ERROR: No valid service configuration found"
    return 1
}

# Verify rollback
verify_rollback() {
    log "Verifying rollback..."
    
    local max_attempts=30
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -f -s --max-time 5 "http://localhost:8000/health" > /dev/null; then
            log "SUCCESS: Service is responding to health checks"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log "Waiting for service to start... ($attempt/$max_attempts)"
        sleep 2
    done
    
    log "ERROR: Service did not start properly after rollback"
    return 1
}

# Main function
main() {
    check_permissions
    
    log "Starting rollback process..."
    log "Target: $ROLLBACK_TARGET"
    
    # Get backup target
    local backup_path
    backup_path=$(get_backup_target "$ROLLBACK_TARGET")
    log "Using backup: $backup_path"
    
    # Stop current service
    stop_service
    
    # Backup current state
    backup_current_state
    
    # Restore from backup
    restore_from_backup "$backup_path"
    
    # Start service
    if start_service; then
        # Verify rollback
        if verify_rollback; then
            log "Rollback completed successfully"
            exit 0
        else
            log "Rollback verification failed"
            exit 1
        fi
    else
        log "Failed to start service after rollback"
        exit 1
    fi
}

# Help function
show_help() {
    cat << EOF
Agent 007 Backend Rollback Script

Usage: $0 [BACKUP_TARGET]

Arguments:
  BACKUP_TARGET    Backup directory name to rollback to
                   'previous' - rollback to most recent backup (default)
                   'list' - list available backups
                   'YYYY-MM-DD-HHMMSS' - rollback to specific backup

Examples:
  $0                           # Rollback to previous version
  $0 previous                  # Rollback to previous version  
  $0 list                      # List available backups
  $0 2024-01-15-143022        # Rollback to specific backup

EOF
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        main
        ;;
esac