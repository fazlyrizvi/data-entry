#!/bin/bash

# Automation System Monitoring Setup Script
# This script sets up the complete monitoring system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DB_NAME="${DB_NAME:-automation_db}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_PASSWORD="${DB_PASSWORD:-}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            DB_HOST="$2"
            shift 2
            ;;
        -p|--port)
            DB_PORT="$2"
            shift 2
            ;;
        -u|--user)
            DB_USER="$2"
            shift 2
            ;;
        -d|--database)
            DB_NAME="$2"
            shift 2
            ;;
        --password)
            DB_PASSWORD="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  -h, --host HOST     Database host (default: localhost)"
            echo "  -p, --port PORT     Database port (default: 5432)"
            echo "  -u, --user USER     Database user (default: postgres)"
            echo "  -d, --database DB   Database name (default: automation_db)"
            echo "  --password PASS     Database password"
            echo "  --dry-run           Show what would be done without executing"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build connection string
export PGPASSWORD="$DB_PASSWORD"
CONN_STRING="-h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${YELLOW}=== Automation System Monitoring Setup ===${NC}"
echo ""
echo "Configuration:"
echo "  Database Host: $DB_HOST"
echo "  Database Port: $DB_PORT"
echo "  Database User: $DB_USER"
echo "  Database Name: $DB_NAME"
echo "  Script Directory: $SCRIPT_DIR"
echo ""

# Check if database connection is valid
echo -e "${YELLOW}Checking database connection...${NC}"
if ! psql $CONN_STRING -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to database${NC}"
    echo "Please check your connection parameters"
    exit 1
fi
echo -e "${GREEN}Database connection successful${NC}"
echo ""

# Check if required extensions are available
echo -e "${YELLOW}Checking required extensions...${NC}"
EXTENSIONS=$(psql $CONN_STRING -t -c "SELECT name FROM pg_available_extensions WHERE name IN ('uuid-ossp', 'pg_stat_statements');")
if echo "$EXTENSIONS" | grep -q "uuid-ossp"; then
    echo -e "${GREEN}✓ uuid-ossp extension available${NC}"
else
    echo -e "${YELLOW}⚠ uuid-ossp extension not available (will try to create)${NC}"
fi

if echo "$EXTENSIONS" | grep -q "pg_stat_statements"; then
    echo -e "${GREEN}✓ pg_stat_statements extension available${NC}"
else
    echo -e "${YELLOW}⚠ pg_stat_statements extension not available${NC}"
fi
echo ""

# Check migration files
echo -e "${YELLOW}Checking migration files...${NC}"
REQUIRED_FILES=(
    "000_main_migration.sql"
    "001_create_processing_metrics.sql"
    "002_create_error_tracking.sql"
    "003_create_performance_monitoring.sql"
    "004_create_system_health.sql"
    "005_create_queue_monitoring.sql"
    "006_create_alerts.sql"
    "007_create_dashboard_views.sql"
    "008_alerting_functions.sql"
    "009_automated_monitoring.sql"
    "010_monitoring_procedures.sql"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$SCRIPT_DIR/$file" ]; then
        echo -e "${GREEN}✓ $file${NC}"
    else
        echo -e "${RED}✗ $file (missing)${NC}"
        exit 1
    fi
done
echo ""

# Dry run option
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN MODE - No changes will be made${NC}"
    echo ""
    echo "The following SQL would be executed:"
    echo "  1. Create database extensions"
    echo "  2. Create monitoring tables"
    echo "  3. Create dashboard views"
    echo "  4. Create monitoring functions"
    echo "  5. Create integration procedures"
    echo "  6. Insert initial data"
    echo "  7. Create indexes"
    echo ""
    exit 0
fi

# Run migration
echo -e "${YELLOW}Running database migration...${NC}"
echo ""

# Create extensions first
echo -e "${YELLOW}Creating extensions...${NC}"
psql $CONN_STRING << EOF
-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Extensions created${NC}"
else
    echo -e "${RED}✗ Failed to create extensions${NC}"
    exit 1
fi
echo ""

# Run main migration
echo -e "${YELLOW}Running main migration...${NC}"
if psql $CONN_STRING -f "$SCRIPT_DIR/000_main_migration.sql" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Migration completed successfully${NC}"
else
    echo -e "${RED}✗ Migration failed${NC}"
    echo "Please check the error messages above"
    exit 1
fi
echo ""

# Verify installation
echo -e "${YELLOW}Verifying installation...${NC}"
TABLES=$(psql $CONN_STRING -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('processing_metrics', 'error_tracking', 'performance_monitoring', 'system_health', 'queue_monitoring', 'alerts');")
FUNCTIONS=$(psql $CONN_STRING -t -c "SELECT count(*) FROM information_schema.routines WHERE routine_schema = 'public' AND routine_type = 'FUNCTION' AND routine_name LIKE '%monitor%';")

echo "Tables created: $TABLES"
echo "Functions created: $FUNCTIONS"
echo ""

if [ "$TABLES" -eq "6" ] && [ "$FUNCTIONS" -ge "15" ]; then
    echo -e "${GREEN}✓ Installation verified successfully${NC}"
else
    echo -e "${YELLOW}⚠ Installation may be incomplete (expected 6 tables, $FUNCTIONS functions found)${NC}"
fi
echo ""

# Show next steps
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "Next steps:"
echo "1. Configure alert thresholds:"
echo "   Edit $SCRIPT_DIR/monitoring_config.json"
echo ""
echo "2. Test the monitoring system:"
echo "   psql $CONN_STRING -c \"SELECT get_dashboard_summary();\""
echo ""
echo "3. Integrate with your application:"
echo "   Use the Python client: $SCRIPT_DIR/integration_example.py"
echo ""
echo "4. Schedule automated checks:"
echo "   - Health checks every 5 minutes"
echo "   - Alert checks every 1 minute"
echo "   - Cleanup daily"
echo ""
echo "Documentation: $SCRIPT_DIR/../docs/monitoring_setup.md"
echo ""

# Create cron job examples
echo -e "${YELLOW}Creating cron job examples...${NC}"
cat > "$SCRIPT_DIR/monitoring_crontab.txt" << 'EOF'
# Automation System Monitoring Cron Jobs
# Add these to your crontab (crontab -e)

# Health checks every 5 minutes
*/5 * * * * psql -h localhost -U postgres -d automation_db -c "SELECT check_system_health_alerts();" 2>/dev/null

# Alert checks every minute
* * * * * psql -h localhost -U postgres -d automation_db -c "SELECT check_error_rate_alerts(); SELECT check_processing_performance_alerts(); SELECT check_queue_backlog_alerts(); SELECT resolve_resolved_alerts();" 2>/dev/null

# Cleanup old data daily at 2 AM
0 2 * * * psql -h localhost -U postgres -d automation_db -c "SELECT cleanup_old_monitoring_data();" 2>/dev/null

# Queue metrics update every 10 minutes
*/10 * * * * psql -h localhost -U postgres -d automation_db -c "SELECT calculate_queue_metrics('default_queue'); SELECT calculate_queue_metrics('priority_queue'); SELECT calculate_queue_metrics('batch_processing');" 2>/dev/null
EOF

echo -e "${GREEN}✓ Cron job examples saved to: $SCRIPT_DIR/monitoring_crontab.txt${NC}"
echo ""

echo -e "${GREEN}Setup complete! The monitoring system is ready to use.${NC}"