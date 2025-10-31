"""
Example: MySQL to PostgreSQL Bidirectional Synchronization

Demonstrates bidirectional synchronization between MySQL and PostgreSQL databases.
"""

import asyncio
import logging
from datetime import datetime, timedelta

# Import database sync components
from enterprise_integration.database_sync.databases import MySQLConfig, MySQLConnector
from enterprise_integration.database_sync.databases import PostgreSQLConfig, PostgreSQLConnector
from enterprise_integration.database_sync.core import (
    SyncManager, SyncConfiguration, SyncMode, SyncDirection,
    ConflictResolver, ConflictStrategy
)
from enterprise_integration.database_sync.transformation import (
    TransformationPipeline, TransformationRule, TransformationType
)
from enterprise_integration.database_sync.cdc import (
    CDCSystem, CDCConfiguration, CDCType
)
from enterprise_integration.database_sync.monitoring import (
    MonitoringSystem, Alert, AlertSeverity
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_mysql_connector():
    """Create and configure MySQL connector."""
    config = MySQLConfig(
        host="localhost",
        port=3306,
        database="inventory_db",
        username="sync_user",
        password="sync_password",
        charset="utf8mb4",
        autocommit=False,
        max_connections=15,
        connect_timeout=10,
        read_timeout=30
    )
    
    connector = MySQLConnector(config)
    await connector.connect()
    
    # Check binlog status for CDC
    if connector.binlog_enabled:
        logger.info("MySQL binlog is enabled for CDC")
        
        # Ensure row-based binlog format
        await connector._ensure_binlog_format_row()
        
        # Setup change tracking
        await connector.create_change_tracking_table()
        
        # Enable CDC for inventory tables
        tables = ["products", "categories", "inventory", "suppliers"]
        await connector.start_cdc(tables)
    else:
        logger.warning("MySQL binlog is not enabled. CDC will not be available.")
    
    return connector


async def create_postgresql_connector():
    """Create and configure PostgreSQL connector."""
    config = PostgreSQLConfig(
        host="localhost",
        port=5432,
        database="inventory_warehouse",
        username="sync_user",
        password="sync_password",
        ssl_mode="prefer",
        max_connections=15,
        application_name="inventory_sync"
    )
    
    connector = PostgreSQLConnector(config)
    await connector.connect()
    
    # Setup logical decoding for CDC
    try:
        await connector.start_cdc(["products", "categories", "inventory", "suppliers"])
        logger.info("PostgreSQL CDC enabled")
    except Exception as e:
        logger.warning(f"PostgreSQL CDC setup failed: {e}")
    
    return connector


class BidirectionalSyncManager:
    """Manager for bidirectional synchronization."""
    
    def __init__(self, mysql_connector, postgresql_connector):
        self.mysql_connector = mysql_connector
        self.postgresql_connector = postgresql_connector
        self.sync_manager = None
        self.cdc_system = None
        self.monitoring = None
        
        # Sync configurations
        self.mysql_to_pg_config = None
        self.pg_to_mysql_config = None
        
        # Conflict resolution
        self.conflict_resolver = ConflictResolver(
            default_strategy=ConflictStrategy.TIMESTAMP_BASED,
            timestamp_field="updated_at",
            version_field="version"
        )
        
        # Transformation pipelines
        self.mysql_to_pg_pipeline = None
        self.pg_to_mysql_pipeline = None
    
    async def initialize(self):
        """Initialize bidirectional synchronization."""
        logger.info("Initializing bidirectional synchronization")
        
        # Setup monitoring
        self.monitoring = MonitoringSystem()
        await self.monitoring.start()
        
        # Create alerts
        await self._create_monitoring_alerts()
        
        # Setup CDC system
        self.cdc_system = CDCSystem()
        await self.cdc_system.start()
        
        # Setup sync manager
        self.sync_manager = SyncManager()
        self.sync_manager.set_sync_manager(self.sync_manager)
        self.sync_manager.set_cdc_system(self.cdc_system)
        await self.sync_manager.start()
        
        # Create transformation pipelines
        self.mysql_to_pg_pipeline = await self._create_mysql_to_pg_pipeline()
        self.pg_to_mysql_pipeline = await self._create_pg_to_mysql_pipeline()
        
        # Create sync configurations
        await self._create_sync_configurations()
        
        logger.info("Bidirectional synchronization initialized")
    
    async def _create_mysql_to_pg_pipeline(self):
        """Create transformation pipeline from MySQL to PostgreSQL."""
        pipeline = TransformationPipeline("mysql_to_postgresql")
        
        # Field mapping
        field_mapping_rule = TransformationRule(
            name="MySQL to PostgreSQL field mapping",
            transformation_type=TransformationType.FIELD_MAPPING,
            metadata={
                'config': {
                    'field_mappings': {
                        'product_id': 'id',
                        'product_name': 'name',
                        'description': 'description',
                        'price': 'price',
                        'category_id': 'category_id',
                        'created_at': 'created_at',
                        'updated_at': 'updated_at',
                        'is_active': 'is_active'
                    },
                    'default_values': {
                        'is_active': True,
                        'source_system': 'mysql'
                    }
                }
            }
        )
        
        # Type conversion
        type_conversion_rule = TransformationRule(
            name="Data type conversion",
            transformation_type=TransformationType.TYPE_CONVERSION,
            metadata={
                'config': {
                    'type_conversions': {
                        'price': 'decimal',
                        'created_at': 'datetime',
                        'updated_at': 'datetime',
                        'is_active': 'boolean'
                    }
                }
            }
        )
        
        # Data enrichment
        enrichment_rule = TransformationRule(
            name="Enrich inventory data",
            transformation_type=TransformationType.DATA_ENRICHMENT,
            metadata={
                'config': {
                    'enrichment': {
                        'add_timestamps': True,
                        'calculated_fields': {
                            'last_synced': {
                                'type': 'format_date',
                                'source_field': 'updated_at',
                                'format': '%Y-%m-%d %H:%M:%S'
                            }
                        }
                    }
                }
            }
        )
        
        pipeline.add_rule(field_mapping_rule)
        pipeline.add_rule(type_conversion_rule)
        pipeline.add_rule(enrichment_rule)
        
        return pipeline
    
    async def _create_pg_to_mysql_pipeline(self):
        """Create transformation pipeline from PostgreSQL to MySQL."""
        pipeline = TransformationPipeline("postgresql_to_mysql")
        
        # Field mapping
        field_mapping_rule = TransformationRule(
            name="PostgreSQL to MySQL field mapping",
            transformation_type=TransformationType.FIELD_MAPPING,
            metadata={
                'config': {
                    'field_mappings': {
                        'id': 'product_id',
                        'name': 'product_name',
                        'description': 'description',
                        'price': 'price',
                        'category_id': 'category_id',
                        'created_at': 'created_at',
                        'updated_at': 'updated_at',
                        'is_active': 'is_active'
                    },
                    'default_values': {
                        'source_system': 'postgresql'
                    }
                }
            }
        )
        
        # Type conversion
        type_conversion_rule = TransformationRule(
            name="Data type conversion",
            transformation_type=TransformationType.TYPE_CONVERSION,
            metadata={
                'config': {
                    'type_conversions': {
                        'price': 'float',
                        'created_at': 'datetime',
                        'updated_at': 'datetime',
                        'is_active': 'boolean'
                    }
                }
            }
        )
        
        pipeline.add_rule(field_mapping_rule)
        pipeline.add_rule(type_conversion_rule)
        
        return pipeline
    
    async def _create_sync_configurations(self):
        """Create sync configurations for both directions."""
        # MySQL to PostgreSQL
        self.mysql_to_pg_config = SyncConfiguration(
            name="MySQL to PostgreSQL Sync",
            source_database_id="mysql_inventory",
            target_database_id="postgresql_warehouse",
            sync_mode=SyncMode.REAL_TIME,
            sync_direction=SyncDirection.SOURCE_TO_TARGET,
            batch_size=100,
            max_concurrent_operations=10,
            conflict_threshold=50,
            transformations={
                'products': self.mysql_to_pg_pipeline.transform_record
            }
        )
        
        # PostgreSQL to MySQL
        self.pg_to_mysql_config = SyncConfiguration(
            name="PostgreSQL to MySQL Sync",
            source_database_id="postgresql_warehouse",
            target_database_id="mysql_inventory",
            sync_mode=SyncMode.REAL_TIME,
            sync_direction=SyncMode.REAL_TIME,  # This creates bidirectional
            batch_size=100,
            max_concurrent_operations=10,
            conflict_threshold=50,
            transformations={
                'products': self.pg_to_mysql_pipeline.transform_record
            }
        )
    
    async def _create_monitoring_alerts(self):
        """Create monitoring alerts."""
        alerts = [
            Alert(
                name="Bidirectional Sync Conflicts",
                description="High number of sync conflicts detected",
                severity=AlertSeverity.WARNING,
                metric_name="sync.conflicts_per_hour",
                condition=">",
                threshold=20.0,
                duration=timedelta(minutes=10)
            ),
            Alert(
                name="Database Lag",
                description="Database synchronization lag is too high",
                severity=AlertSeverity.ERROR,
                metric_name="sync.lag_seconds",
                condition=">",
                threshold=60.0,
                duration=timedelta(minutes=5)
            ),
            Alert(
                name="CDC Processing Errors",
                description="CDC processing errors detected",
                severity=AlertSeverity.ERROR,
                metric_name="cdc.processing_errors",
                condition=">",
                threshold=5.0,
                duration=timedelta(minutes=2)
            )
        ]
        
        for alert in alerts:
            await self.monitoring.create_alert(alert)
    
    async def start_synchronization(self):
        """Start bidirectional synchronization."""
        logger.info("Starting bidirectional synchronization")
        
        # Create sync configurations
        mysql_to_pg_id = await self.sync_manager.create_sync_configuration(self.mysql_to_pg_config)
        pg_to_mysql_id = await self.sync_manager.create_sync_configuration(self.pg_to_mysql_config)
        
        # Start both synchronizations
        mysql_to_pg_success = await self.sync_manager.start_sync(mysql_to_pg_id)
        pg_to_mysql_success = await self.sync_manager.start_sync(pg_to_mysql_id)
        
        if mysql_to_pg_success and pg_to_mysql_success:
            logger.info("Both synchronizations started successfully")
            return mysql_to_pg_id, pg_to_mysql_id
        else:
            logger.error("Failed to start one or both synchronizations")
            return None, None
    
    async def monitor_synchronization(self, sync_ids):
        """Monitor bidirectional synchronization."""
        logger.info("Starting synchronization monitoring")
        
        mysql_to_pg_id, pg_to_mysql_id = sync_ids
        
        try:
            while True:
                # Get status of both synchronizations
                mysql_to_pg_status = await self.sync_manager.get_sync_status(mysql_to_pg_id)
                pg_to_mysql_status = await self.sync_manager.get_sync_status(pg_to_mysql_id)
                
                if mysql_to_pg_status and pg_to_mysql_status:
                    logger.info(f"MySQL→PG: {mysql_to_pg_status['status']} "
                              f"(Events: {mysql_to_pg_status['events_processed']}, "
                              f"Conflicts: {mysql_to_pg_status['conflicts_detected']})")
                    
                    logger.info(f"PG→MySQL: {pg_to_mysql_status['status']} "
                              f"(Events: {pg_to_mysql_status['events_processed']}, "
                              f"Conflicts: {pg_to_mysql_status['conflicts_detected']})")
                    
                    # Record metrics
                    await self.monitoring.record_metric(
                        "bidirectional.sync_mysql_to_pg_events",
                        mysql_to_pg_status['events_processed']
                    )
                    await self.monitoring.record_metric(
                        "bidirectional.sync_pg_to_mysql_events",
                        pg_to_mysql_status['events_processed']
                    )
                    await self.monitoring.record_metric(
                        "bidirectional.conflicts_detected",
                        mysql_to_pg_status['conflicts_detected'] + pg_to_mysql_status['conflicts_detected']
                    )
                
                # Get global statistics
                global_stats = await self.sync_manager.get_global_statistics()
                logger.debug(f"Global Sync Stats: Active={global_stats.get('active_syncs')}, "
                           f"Total Events={global_stats.get('total_events_processed')}")
                
                await asyncio.sleep(60)  # Monitor every minute
                
        except KeyboardInterrupt:
            logger.info("Received stop signal")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
    
    async def stop_synchronization(self, sync_ids):
        """Stop bidirectional synchronization."""
        logger.info("Stopping bidirectional synchronization")
        
        mysql_to_pg_id, pg_to_mysql_id = sync_ids
        
        if mysql_to_pg_id:
            await self.sync_manager.stop_sync(mysql_to_pg_id)
        if pg_to_mysql_id:
            await self.sync_manager.stop_sync(pg_to_mysql_id)
        
        await self.sync_manager.stop()
    
    async def cleanup(self):
        """Cleanup all resources."""
        logger.info("Cleaning up bidirectional synchronization")
        
        await self.monitoring.stop()
        await self.cdc_system.stop()
        
        await self.mysql_connector.disconnect()
        await self.postgresql_connector.disconnect()
        
        logger.info("Cleanup completed")


async def demo_manual_synchronization():
    """Demonstrate manual synchronization."""
    logger.info("Starting manual synchronization demo")
    
    mysql_connector = await create_mysql_connector()
    pg_connector = await create_postgresql_connector()
    
    try:
        # Manual data sync
        logger.info("Executing manual product synchronization")
        
        # Get products from MySQL
        mysql_products = await mysql_connector.execute_query(
            "SELECT * FROM products WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)"
        )
        logger.info(f"Retrieved {len(mysql_products)} products from MySQL")
        
        # Transform and sync to PostgreSQL
        bidirectional_manager = BidirectionalSyncManager(mysql_connector, pg_connector)
        pipeline = await bidirectional_manager._create_mysql_to_pg_pipeline()
        
        for product in mysql_products:
            try:
                # Transform product
                result = await pipeline.transform_record(product)
                
                if result.success:
                    # Convert to SyncOperation
                    sync_op = type('SyncOperation', (), {
                        'operation_id': f"manual_sync_{product['product_id']}",
                        'source_table': 'products',
                        'target_table': 'products',
                        'operation_type': 'INSERT',
                        'data': result.transformed_data,
                        'timestamp': datetime.now()
                    })()
                    
                    # Insert into PostgreSQL
                    await pg_connector.execute_operation(sync_op)
                    logger.debug(f"Synced product {product['product_id']}")
                else:
                    logger.warning(f"Transformation failed for product {product['product_id']}: {result.errors}")
            
            except Exception as e:
                logger.error(f"Failed to sync product {product['product_id']}: {e}")
        
        logger.info("Manual synchronization completed")
        
    finally:
        await mysql_connector.disconnect()
        await pg_connector.disconnect()


async def demo_conflict_detection():
    """Demonstrate conflict detection in bidirectional sync."""
    logger.info("Starting conflict detection demo")
    
    from enterprise_integration.database_sync.core import ConflictResolver, ConflictStrategy
    
    # Create conflict resolver
    resolver = ConflictResolver(
        default_strategy=ConflictStrategy.TIMESTAMP_BASED,
        timestamp_field="updated_at",
        version_field="version"
    )
    
    # Simulate product data conflict
    mysql_data = {
        'product_id': 'PROD123',
        'product_name': 'Widget Pro',
        'price': 99.99,
        'updated_at': datetime.now(),
        'version': 2
    }
    
    pg_data = {
        'id': 'PROD123',
        'name': 'Widget Pro',
        'price': 89.99,  # Different price
        'updated_at': datetime.now() - timedelta(minutes=5),  # Older timestamp
        'version': 1
    }
    
    # Detect conflicts
    conflicts = await resolver.detect_conflicts(
        source_data=mysql_data,
        target_data=pg_data,
        table_name="products",
        primary_key={'product_id': 'PROD123'}
    )
    
    logger.info(f"Detected {len(conflicts)} conflicts")
    
    for conflict in conflicts:
        logger.info(f"Conflict: {conflict.conflict_type.value} in fields {conflict.conflicting_fields}")
        logger.info(f"MySQL data: {conflict.source_data}")
        logger.info(f"PostgreSQL data: {conflict.target_data}")
    
    # Resolve conflicts
    resolution_results = await resolver.resolve_conflicts(conflicts)
    
    for result in resolution_results:
        if result.resolved:
            logger.info(f"Resolved conflict using {result.strategy.value}")
            logger.info(f"Resolved data: {result.resolved_data}")
        else:
            logger.error(f"Conflict resolution failed: {result.error_message}")


async def demo_performance_monitoring():
    """Demonstrate performance monitoring."""
    logger.info("Starting performance monitoring demo")
    
    monitoring = MonitoringSystem()
    await monitoring.start()
    
    try:
        # Simulate performance metrics
        for i in range(10):
            await monitoring.record_metric(
                "sync.throughput_events_per_second",
                50 + (i * 5)  # Increasing throughput
            )
            
            await monitoring.record_metric(
                "sync.average_latency_ms",
                100 - (i * 3)  # Decreasing latency
            )
            
            await monitoring.record_metric(
                "database.connection_pool_usage",
                0.3 + (i * 0.05)  # Increasing pool usage
            )
            
            await monitoring.increment_counter("sync.total_events_processed", 100)
            
            await asyncio.sleep(1)
        
        # Get performance summary
        summary = await monitoring.get_performance_summary()
        logger.info(f"Performance Summary: {summary}")
        
        # Get detailed metrics
        metrics = await monitoring.get_metrics()
        logger.info(f"Metrics collected: {len(metrics)} metric types")
        
    finally:
        await monitoring.stop()


async def main():
    """Main demo function."""
    logger.info("Bidirectional MySQL to PostgreSQL Synchronization Demo")
    logger.info("=======================================================")
    
    try:
        # Initialize bidirectional sync manager
        mysql_connector = await create_mysql_connector()
        pg_connector = await create_postgresql_connector()
        
        bidirectional_manager = BidirectionalSyncManager(mysql_connector, pg_connector)
        await bidirectional_manager.initialize()
        
        # Start synchronization
        sync_ids = await bidirectional_manager.start_synchronization()
        
        if sync_ids[0] and sync_ids[1]:
            # Monitor synchronization
            await bidirectional_manager.monitor_synchronization(sync_ids)
        else:
            logger.error("Failed to start synchronization")
        
    except KeyboardInterrupt:
        logger.info("Received stop signal")
    except Exception as e:
        logger.error(f"Demo error: {e}")
    finally:
        if 'bidirectional_manager' in locals():
            await bidirectional_manager.cleanup()
        
        logger.info("Bidirectional synchronization demo completed")


if __name__ == "__main__":
    # Note: This example requires running MySQL and PostgreSQL instances
    # Update the connection configurations as needed for your environment
    
    # You can run individual demos:
    # asyncio.run(demo_manual_synchronization())
    # asyncio.run(demo_conflict_detection())
    # asyncio.run(demo_performance_monitoring())
    
    asyncio.run(main())
