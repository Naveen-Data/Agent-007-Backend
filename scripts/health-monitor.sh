#!/bin/bash

# Production Health Monitoring Script for Agent 007 Backend

set -euo pipefail

# Configuration
BACKEND_URL=${EC2_HOST:-"localhost"}
BACKEND_PORT=${BACKEND_PORT:-8000}
HEALTH_CHECK_INTERVAL=${HEALTH_CHECK_INTERVAL:-30}
HEALTH_CHECK_TIMEOUT=${HEALTH_CHECK_TIMEOUT:-10}
MAX_RETRIES=3
LOG_FILE="/var/log/agent007/health-monitor.log"
ALERT_EMAIL=${ALERT_EMAIL:-""}

# Create log directory if it doesn't exist
sudo mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log() {
    local level=$1
    shift
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $*" | sudo tee -a "$LOG_FILE"
}

# Health check function
check_health() {
    local url="http://${BACKEND_URL}:${BACKEND_PORT}/health"
    
    # Check if service is responding
    if curl -f -s --max-time "$HEALTH_CHECK_TIMEOUT" "$url" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Check service status
check_service_status() {
    if systemctl is-active --quiet agent007-backend; then
        return 0
    else
        return 1
    fi
}

# Check Docker container status
check_docker_status() {
    if docker ps --filter "name=agent007-backend" --filter "status=running" --quiet | grep -q .; then
        return 0
    else
        return 1
    fi
}

# Check system resources
check_resources() {
    local cpu_usage memory_usage disk_usage
    
    # CPU usage (load average)
    cpu_usage=$(uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $1}' | tr -d ' ')
    
    # Memory usage percentage
    memory_usage=$(free | grep Mem | awk '{printf "%.1f", ($3/$2) * 100.0}')
    
    # Disk usage percentage
    disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    log "INFO" "System resources - CPU: ${cpu_usage}, Memory: ${memory_usage}%, Disk: ${disk_usage}%"
    
    # Alert thresholds
    if (( $(echo "$memory_usage > 85" | bc -l) )); then
        log "WARN" "High memory usage: ${memory_usage}%"
        return 1
    fi
    
    if [[ $disk_usage -gt 90 ]]; then
        log "WARN" "High disk usage: ${disk_usage}%"
        return 1
    fi
    
    return 0
}

# Restart service function
restart_service() {
    log "WARN" "Attempting to restart Agent 007 backend service..."
    
    # Try Docker restart first
    if docker ps --filter "name=agent007-backend" --quiet | grep -q .; then
        docker restart agent007-backend
        sleep 10
        if check_docker_status && check_health; then
            log "INFO" "Service restarted successfully via Docker"
            return 0
        fi
    fi
    
    # Try systemctl restart
    if systemctl is-enabled --quiet agent007-backend 2>/dev/null; then
        sudo systemctl restart agent007-backend
        sleep 10
        if check_service_status && check_health; then
            log "INFO" "Service restarted successfully via systemctl"
            return 0
        fi
    fi
    
    log "ERROR" "Failed to restart service"
    return 1
}

# Send alert function
send_alert() {
    local message=$1
    local severity=${2:-"WARNING"}
    
    log "$severity" "$message"
    
    # Send email if configured
    if [[ -n "$ALERT_EMAIL" ]] && command -v mail >/dev/null; then
        echo "$message" | mail -s "Agent 007 Backend Alert: $severity" "$ALERT_EMAIL"
    fi
    
    # Log to syslog
    logger -t "agent007-monitor" -p "user.$severity" "$message"
}

# Main monitoring loop
main() {
    log "INFO" "Starting Agent 007 backend health monitor..."
    
    local consecutive_failures=0
    
    while true; do
        # Health check
        if check_health; then
            if [[ $consecutive_failures -gt 0 ]]; then
                log "INFO" "Service recovered after $consecutive_failures failures"
                send_alert "Service is healthy again" "INFO"
            fi
            consecutive_failures=0
            log "INFO" "Health check passed"
        else
            consecutive_failures=$((consecutive_failures + 1))
            log "WARN" "Health check failed (attempt $consecutive_failures/$MAX_RETRIES)"
            
            # Try to restart after max retries
            if [[ $consecutive_failures -ge $MAX_RETRIES ]]; then
                send_alert "Service health check failed $MAX_RETRIES times. Attempting restart." "ERROR"
                
                if restart_service; then
                    consecutive_failures=0
                    send_alert "Service restarted successfully" "INFO"
                else
                    send_alert "Failed to restart service. Manual intervention required." "CRITICAL"
                fi
            fi
        fi
        
        # Resource check
        if ! check_resources; then
            send_alert "System resources are running low" "WARNING"
        fi
        
        sleep "$HEALTH_CHECK_INTERVAL"
    done
}

# Signal handlers
cleanup() {
    log "INFO" "Health monitor stopping..."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Run main function
main