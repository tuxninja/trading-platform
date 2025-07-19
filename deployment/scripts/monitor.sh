#!/bin/bash
# Monitor Trading Platform deployment

set -e

# Configuration
EC2_HOST=${EC2_HOST:-}
EC2_USER=${EC2_USER:-ec2-user}
SSH_KEY_PATH=${SSH_KEY_PATH:-~/.ssh/trading-platform}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    clear
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE} Trading Platform Monitoring Dashboard${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo -e "${YELLOW}Host: $EC2_HOST${NC}"
    echo -e "${YELLOW}Time: $(date)${NC}"
    echo ""
}

check_service_health() {
    echo -e "${BLUE}🏥 Service Health Status${NC}"
    echo "================================="
    
    # Frontend health
    if curl -f -s "http://$EC2_HOST/health" >/dev/null 2>&1; then
        echo -e "Frontend:     ${GREEN}✅ Healthy${NC}"
    else
        echo -e "Frontend:     ${RED}❌ Unhealthy${NC}"
    fi
    
    # Backend health
    if curl -f -s "http://$EC2_HOST:8000/" >/dev/null 2>&1; then
        echo -e "Backend API:  ${GREEN}✅ Healthy${NC}"
    else
        echo -e "Backend API:  ${RED}❌ Unhealthy${NC}"
    fi
    
    # Database health (check if backend can respond)
    if curl -f -s "http://$EC2_HOST:8000/api/performance" >/dev/null 2>&1; then
        echo -e "Database:     ${GREEN}✅ Connected${NC}"
    else
        echo -e "Database:     ${RED}❌ Connection Issues${NC}"
    fi
    echo ""
}

show_container_status() {
    echo -e "${BLUE}🐳 Container Status${NC}"
    echo "================================="
    ssh -i $SSH_KEY_PATH -o StrictHostKeyChecking=no $EC2_USER@$EC2_HOST << 'EOF'
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -10
EOF
    echo ""
}

show_system_resources() {
    echo -e "${BLUE}💻 System Resources${NC}"
    echo "================================="
    ssh -i $SSH_KEY_PATH -o StrictHostKeyChecking=no $EC2_USER@$EC2_HOST << 'EOF'
        echo "Memory Usage:"
        free -h
        echo ""
        echo "Disk Usage:"
        df -h /opt/trading /
        echo ""
        echo "CPU Usage (current):"
        top -bn1 | grep "Cpu(s)" | awk '{print $2 $3 $4 $5 $6 $7 $8}'
        echo ""
        echo "Load Average:"
        uptime
EOF
    echo ""
}

show_recent_logs() {
    echo -e "${BLUE}📋 Recent Application Logs${NC}"
    echo "================================="
    ssh -i $SSH_KEY_PATH -o StrictHostKeyChecking=no $EC2_USER@$EC2_HOST << 'EOF'
        echo "Backend Logs (last 10 lines):"
        docker logs trading-backend --tail 10 2>/dev/null || echo "No backend logs available"
        echo ""
        echo "Frontend Logs (last 5 lines):"
        docker logs trading-frontend --tail 5 2>/dev/null || echo "No frontend logs available"
        echo ""
        echo "System Logs (last 5 lines):"
        tail -5 /var/log/messages 2>/dev/null || tail -5 /var/log/syslog 2>/dev/null || echo "No system logs available"
EOF
    echo ""
}

show_network_stats() {
    echo -e "${BLUE}🌐 Network & Performance${NC}"
    echo "================================="
    
    # Response time test
    echo "Response Time Tests:"
    
    # Frontend
    FRONTEND_TIME=$(curl -o /dev/null -s -w '%{time_total}' "http://$EC2_HOST/" || echo "N/A")
    echo -e "  Frontend:     ${FRONTEND_TIME}s"
    
    # Backend API
    BACKEND_TIME=$(curl -o /dev/null -s -w '%{time_total}' "http://$EC2_HOST:8000/" || echo "N/A")
    echo -e "  Backend API:  ${BACKEND_TIME}s"
    
    # Database query
    API_TIME=$(curl -o /dev/null -s -w '%{time_total}' "http://$EC2_HOST:8000/api/performance" || echo "N/A")
    echo -e "  API Query:    ${API_TIME}s"
    
    echo ""
    
    # Connection stats
    ssh -i $SSH_KEY_PATH -o StrictHostKeyChecking=no $EC2_USER@$EC2_HOST << 'EOF'
        echo "Network Connections:"
        netstat -an | grep -E ':(80|443|8000)' | wc -l | awk '{print "  Active connections: " $1}'
        echo ""
EOF
}

show_application_metrics() {
    echo -e "${BLUE}📊 Application Metrics${NC}"
    echo "================================="
    
    # Get performance metrics from API
    METRICS=$(curl -s "http://$EC2_HOST:8000/api/performance" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$METRICS" ]; then
        echo "Trading Performance:"
        echo "$METRICS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'  Total Trades:     {data.get(\"total_trades\", \"N/A\")}')
    print(f'  Win Rate:         {data.get(\"win_rate\", \"N/A\")}%')
    print(f'  Current Balance:  \${data.get(\"current_balance\", \"N/A\")}')
    print(f'  Total Return:     {data.get(\"total_return\", \"N/A\")}%')
    print(f'  P&L:              \${data.get(\"total_profit_loss\", \"N/A\")}')
except:
    print('  Unable to parse metrics')
" 2>/dev/null
    else
        echo -e "  ${RED}Unable to fetch application metrics${NC}"
    fi
    
    echo ""
    
    # Database stats
    ssh -i $SSH_KEY_PATH -o StrictHostKeyChecking=no $EC2_USER@$EC2_HOST << 'EOF'
        echo "Database Statistics:"
        if [ -f /opt/trading/data/trading.db ]; then
            DB_SIZE=$(ls -lh /opt/trading/data/trading.db | awk '{print $5}')
            echo "  Database Size:    $DB_SIZE"
            
            # Count records
            TRADE_COUNT=$(sqlite3 /opt/trading/data/trading.db "SELECT COUNT(*) FROM trades;" 2>/dev/null || echo "N/A")
            echo "  Total Trades:     $TRADE_COUNT"
            
            SENTIMENT_COUNT=$(sqlite3 /opt/trading/data/trading.db "SELECT COUNT(*) FROM sentiment_data;" 2>/dev/null || echo "N/A")
            echo "  Sentiment Records: $SENTIMENT_COUNT"
        else
            echo "  Database not found"
        fi
EOF
    echo ""
}

interactive_mode() {
    while true; do
        print_header
        check_service_health
        show_container_status
        show_system_resources
        show_recent_logs
        show_network_stats
        show_application_metrics
        
        echo -e "${YELLOW}Press 'q' to quit, 'r' to refresh, or wait 30 seconds for auto-refresh...${NC}"
        
        read -t 30 -n 1 input
        case $input in
            q|Q)
                echo -e "\n${GREEN}Monitoring stopped.${NC}"
                exit 0
                ;;
            r|R)
                continue
                ;;
            *)
                continue
                ;;
        esac
    done
}

one_time_check() {
    print_header
    check_service_health
    show_container_status
    show_system_resources
    show_application_metrics
}

# Main function
main() {
    if [ -z "$EC2_HOST" ]; then
        echo -e "${RED}❌ EC2_HOST environment variable is not set${NC}"
        echo "Set it with: export EC2_HOST=your-ec2-ip-address"
        exit 1
    fi
    
    case "${1:-interactive}" in
        "interactive")
            interactive_mode
            ;;
        "once")
            one_time_check
            ;;
        "health")
            check_service_health
            ;;
        "containers")
            show_container_status
            ;;
        "resources")
            show_system_resources
            ;;
        "logs")
            show_recent_logs
            ;;
        "metrics")
            show_application_metrics
            ;;
        *)
            echo "Usage: $0 [interactive|once|health|containers|resources|logs|metrics]"
            echo "  interactive  - Continuous monitoring dashboard (default)"
            echo "  once        - One-time status check"
            echo "  health      - Service health check only"
            echo "  containers  - Container status only"
            echo "  resources   - System resources only"
            echo "  logs        - Recent logs only"
            echo "  metrics     - Application metrics only"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"