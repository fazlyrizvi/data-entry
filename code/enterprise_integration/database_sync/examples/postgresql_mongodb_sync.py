"""
Example: PostgreSQL to MongoDB Synchronization

Demonstrates real-time synchronization from PostgreSQL to MongoDB.
"""

import asyncio
import logging
from datetime import datetime, timedelta

# Import database sync components
from enterprise_integration.database_sync.databases import PostgreSQLConfig, PostgreSQLConnector
from enterprise_integration.database_sync.databases import MongoDBConfig, MongoDBConnector
from enterprise_integration.database_sync.core import (
    SyncManager, SyncConfiguration, SyncMode, SyncDirection
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


async def create_postgresql_connector():
    """Create and configure PostgreSQL connector."""
    config = PostgreSQLConfig(
        host="localhost",
        port=5432,
        database="ecommerce",
        username="sync_user",
        password="sync_password",
        ssl_mode="prefer",
        max_connections=10,
        application_name="ecommerce_sync"
    )
    
    connector = PostgreSQLConnector(config)
    await connector.connect()
    
    # Setup change tracking for CDC
    await connector.create_change_tracking_table()
    
    # Enable CDC for tables
    tables = ["customers", "orders", "products", "order_items"]
    await connector.start_cdc(tables)
    
    return connector


async def create_mongodb_connector():
    """Create and configure MongoDB connector."""
    config = MongoDBConfig(
        host="localhost",
        port=27017,
        database="ecommerce_analytics",
        username="sync_user",
        password="sync_password",
        auth_source="admin",
        max_pool_size=20,
        min_pool_size=5,
        retry_writes=True,
        retry_reads=True
    )
    
    connector = MongoDBConnector(config)
    await connector.connect()
    
    return connector


async def setup_transformation_pipeline():
    """Setup data transformation pipeline."""
    pipeline = TransformationPipeline("ecommerce_sync_pipeline")
    
    # Field mapping rule
    field_mapping_rule = TransformationRule(
        name="Map PostgreSQL to MongoDB fields",
        transformation_type=TransformationType.FIELD_MAPPING,
        metadata={
            'config': {
                'field_mappings': {
                    'customer_id': '_id',
                    'first_name': 'firstName',
                    'last_name': 'lastName',
                    'email_address': 'email',
                    'created_at': 'createdAt',
                    'updated_at': 'updatedAt'
                },
                'default_values': {
                    'status': 'active',
                    'source': 'postgresql'
                }
            }
        }
    )
    
    # Data enrichment rule
    enrichment_rule = TransformationRule(
        name="Enrich customer data",
        transformation_type=TransformationType.DATA_ENRICHMENT,
        metadata={
            'config': {
                'enrichment': {
                    'add_timestamps': True,
                    'calculated_fields': {
                        'fullName': {
                            'type': 'concatenate',
                            'fields': ['first_name', 'last_name'],
                            'separator': ' '
                        },
                        'accountAge': {
                            'type': 'count',
                            'fields': ['created_at']
                        }
                    }
                }
            }
        }
    )
    
    # Validation rule
    validation_rule = TransformationRule(
        name="Validate customer data",
        transformation_type=TransformationType.VALIDATION,
        metadata={
            'config': {
                'validation_rules': {
                    'required_fields': ['customer_id', 'email_address'],
                    'format_rules': {
                        'email_address': r'^[^@]+@[^@]+\.[^@]+$'
                    }
                }
            }
        }
    )
    
    pipeline.add_rule(field_mapping_rule)
    pipeline.add_rule(enrichment_rule)
    pipeline.add_rule(validation_rule)
    
    return pipeline


async def setup_monitoring():
    """Setup monitoring and alerting."""
    monitoring = MonitoringSystem()
    await monitoring.start()
    
    # Create alerts
    alerts = [
        Alert(
            name="High Sync Error Rate",
            description="Synchronization error rate is above threshold",
            severity=AlertSeverity.ERROR,
            metric_name="sync.errors_per_minute",
            condition=">",
            threshold=10.0,
            duration=timedelta(minutes=5)
        ),
        Alert(
            name="CDC Lag Detected",
            description="Change data capture lag is too high",
            severity=AlertSeverity.WARNING,
            metric_name="cdc.lag_seconds",
            condition=">",
            threshold=30.0,
            duration=timedelta(minutes=2)
        ),
        Alert(
            name="Database Connection Issues",
            description="Database connection problems detected",
            severity=AlertSeverity.CRITICAL,
            metric_name="database.connection_errors",
            condition=">",
            threshold=0.0,
            duration=timedelta(seconds=0)
        )
    ]
    
    for alert in alerts:
        await monitoring.create_alert(alert)
    
    return monitoring


async def setup_cdc_system():
    """Setup Change Data Capture system."""
    cdc_system = CDCSystem()
    await cdc_system.start()
    
    # Configure CDC for PostgreSQL
    pg_cdc_config = CDCConfiguration(
        name="PostgreSQL to MongoDB CDC",
        source_database_id="postgresql_source",
        target_database_id="mongodb_target",
        cdc_type=CDCType.LOGICAL_DECODING,
        tables=["customers", "orders", "products", "order_items"],
        batch_size=100,
        poll_interval=1.0,
        max_lag_seconds=10,
        retry_attempts=3
    )
    
    cdc_id = await cdc_system.create_cdc_configuration(pg_cdc_config)
    await cdc_system.start_cdc(cdc_id)
    
    return cdc_system, cdc_id


async def sync_postgresql_to_mongodb():
    """Main synchronization function."""
    try:
        logger.info("Starting PostgreSQL to MongoDB synchronization")
        
        # Create connectors
        logger.info("Creating database connectors")
        pg_connector = await create_postgresql_connector()
        mongo_connector = await create_mongodb_connector()
        
        # Setup transformation pipeline
        logger.info("Setting up transformation pipeline")
        pipeline = await setup_transformation_pipeline()
        
        # Setup monitoring
        logger.info("Setting up monitoring")
        monitoring = await setup_monitoring()
        
        # Setup CDC system
        logger.info("Setting up CDC system")
        cdc_system, cdc_id = await setup_cdc_system()
        
        # Create sync configuration
        sync_config = SyncConfiguration(
            name="PostgreSQL to MongoDB Real-time Sync",
            source_database_id="postgresql_source",
            target_database_id="mongodb_target",
            sync_mode=SyncMode.REAL_TIME,
            sync_direction=SyncDirection.SOURCE_TO_TARGET,
            batch_size=50,
            max_concurrent_operations=5,
            conflict_threshold=20,
            transformations={
                'customer_data': pipeline.transform_record
            }
        )
        
        # Create and start sync manager
        sync_manager = SyncManager()
        sync_manager.set_monitoring_system(monitoring)
        await sync_manager.start()
        
        sync_id = await sync_manager.create_sync_configuration(sync_config)
        logger.info(f"Created sync configuration: {sync_id}")
        
        # Start synchronization
        success = await sync_manager.start_sync(sync_id)
        if success:
            logger.info("Synchronization started successfully")
        else:
            logger.error("Failed to start synchronization")
            return
        
        # Record initial metrics
        await monitoring.record_metric("sync.started", 1.0)
        await monitoring.increment_counter("sync.configurations_created")
        
        # Keep the system running
        logger.info("Synchronization is running. Press Ctrl+C to stop.")
        
        try:
            while True:
                # Check system health
                status = await sync_manager.get_sync_status(sync_id)
                if status:
                    logger.info(f"Sync Status: {status['status']}, Events Processed: {status['events_processed']}")
                
                # Record performance metrics
                if status:
                    await monitoring.record_metric(
                        "sync.events_processed_total",
                        status['events_processed']
                    )
                
                # Get monitoring summary
                summary = await monitoring.get_performance_summary()
                logger.debug(f"Monitoring Summary: Active Syncs: {summary['sync_manager']['active_syncs']}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            logger.info("Received stop signal, shutting down...")
        
        # Cleanup
        logger.info("Stopping synchronization")
        await sync_manager.stop_sync(sync_id)
        await sync_manager.stop()
        
        logger.info("Stopping CDC system")
        await cdc_system.stop_cdc(cdc_id)
        await cdc_system.stop()
        
        logger.info("Stopping monitoring")
        await monitoring.stop()
        
        logger.info("Disconnecting from databases")
        await pg_connector.disconnect()
        await mongo_connector.disconnect()
        
        logger.info("PostgreSQL to MongoDB synchronization completed")
        
    except Exception as e:
        logger.error(f"Synchronization error: {e}")
        raise


async def demo_batch_synchronization():
    """Demonstrate batch synchronization."""
    logger.info("Starting batch synchronization demo")
    
    # Create connectors
    pg_connector = await create_postgresql_connector()
    mongo_connector = await create_mongodb_connector()
    
    try:
        # Execute batch sync for a specific table
        logger.info("Executing batch synchronization for customers table")
        
        # Get data from PostgreSQL
        pg_data = await pg_connector.execute_query(
            "SELECT * FROM customers WHERE created_at >= NOW() - INTERVAL '1 day'"
        )
        logger.info(f"Retrieved {len(pg_data)} records from PostgreSQL")
        
        # Transform and sync to MongoDB
        pipeline = await setup_transformation_pipeline()
        
        for record in pg_data:
            # Transform record
            result = await pipeline.transform_record(record)
            
            if result.success:
                # Insert into MongoDB
                mongo_record = result.transformed_data
                await mongo_connector.execute_operation(
                    type('SyncOperation', (), {
                        'operation_type': 'INSERT',
                        'target_table': 'customers',
                        'data': mongo_record,
                        'timestamp': datetime.now()
                    })()
                )
            else:
                logger.warning(f"Transformation failed for record {record.get('customer_id')}: {result.errors}")
        
        logger.info("Batch synchronization completed")
        
    finally:
        await pg_connector.disconnect()
        await mongo_connector.disconnect()


async def demo_conflict_resolution():
    """Demonstrate conflict resolution."""
    logger.info("Starting conflict resolution demo")
    
    from enterprise_integration.database_sync.core import ConflictResolver, ConflictStrategy
    
    # Create conflict resolver
    resolver = ConflictResolver(
        default_strategy=ConflictStrategy.TIMESTAMP_BASED,
        timestamp_field="updated_at"
    )
    
    # Simulate conflicting data
    source_data = {
        'customer_id': '123',
        'name': 'John Doe',
        'email': 'john@example.com',
        'status': 'active',
        'updated_at': datetime.now()
    }
    
    target_data = {
        'customer_id': '123',
        'name': 'John Doe',
        'email': 'john.doe@company.com',
        'status': 'inactive',
        'updated_at': datetime.now() - timedelta(minutes=5)
    }
    
    # Detect conflicts
    conflicts = await resolver.detect_conflicts(
        source_data=source_data,
        target_data=target_data,
        table_name="customers",
        primary_key={'customer_id': '123'}
    )
    
    logger.info(f"Detected {len(conflicts)} conflicts")
    
    # Resolve conflicts
    resolution_results = await resolver.resolve_conflicts(conflicts)
    
    for result in resolution_results:
        if result.resolved:
            logger.info(f"Conflict resolved: {result.resolution_details}")
            logger.info(f"Resolved data: {result.resolved_data}")
        else:
            logger.error(f"Conflict resolution failed: {result.error_message}")


async def demo_error_recovery():
    """Demonstrate error recovery."""
    logger.info("Starting error recovery demo")
    
    from enterprise_integration.database_sync.core import ErrorRecovery, RecoveryStrategy
    
    # Create error recovery system
    error_recovery = ErrorRecovery(
        max_retries=3,
        retry_delay_base=1.0,
        retry_delay_max=60.0
    )
    
    await error_recovery.start()
    
    try:
        # Simulate database operations with errors
        async def simulate_failing_operation():
            # This would normally be a database operation
            raise Exception("Simulated database connection error")
        
        # Handle operation with error recovery
        try:
            await error_recovery.handle_operation_error(
                simulate_failing_operation,
                operation_context={
                    'operation_id': 'demo_operation_1',
                    'database_id': 'postgresql',
                    'table_name': 'customers'
                }
            )
            logger.info("Operation completed successfully after error recovery")
        except Exception as e:
            logger.error(f"Operation failed even after recovery attempts: {e}")
        
        # Get error statistics
        stats = error_recovery.get_error_statistics()
        logger.info(f"Error recovery statistics: {stats}")
        
    finally:
        await error_recovery.stop()


async def demo_monitoring_alerts():
    """Demonstrate monitoring and alerts."""
    logger.info("Starting monitoring alerts demo")
    
    monitoring = await setup_monitoring()
    
    try:
        # Simulate various metrics
        await monitoring.record_metric("sync.events_processed", 100)
        await monitoring.record_metric("sync.errors_per_minute", 5)
        await monitoring.record_metric("cdc.lag_seconds", 15)
        
        await monitoring.increment_counter("sync.total_events")
        await monitoring.increment_counter("sync.errors", 2)
        
        # Simulate performance data
        await monitoring.record_metric("sync.throughput_events_per_second", 10.5)
        await monitoring.record_metric("database.connection_pool_usage", 0.75)
        
        # Get monitoring summary
        summary = await monitoring.get_performance_summary()
        logger.info(f"Monitoring summary: {summary}")
        
        # Get current alerts
        active_alerts = await monitoring.get_alerts(AlertStatus.ACTIVE)
        logger.info(f"Active alerts: {len(active_alerts)}")
        
        for alert in active_alerts:
            logger.warning(f"Active Alert: {alert.name} - {alert.description}")
        
        # Simulate alert resolution
        if active_alerts:
            alert = active_alerts[0]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            logger.info(f"Resolved alert: {alert.name}")
        
    finally:
        await monitoring.stop()


async def main():
    """Main demo function."""
    logger.info("Database Synchronization System Demo")
    logger.info("=====================================")
    
    try:
        # Run all demonstrations
        logger.info("\n1. Real-time PostgreSQL to MongoDB Synchronization")
        await sync_postgresql_to_mongodb()
        
        logger.info("\n2. Batch Synchronization Demo")
        await demo_batch_synchronization()
        
        logger.info("\n3. Conflict Resolution Demo")
        await demo_conflict_resolution()
        
        logger.info("\n4. Error Recovery Demo")
        await demo_error_recovery()
        
        logger.info("\n5. Monitoring and Alerts Demo")
        await demo_monitoring_alerts()
        
        logger.info("\nAll demos completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    # Note: This example requires running PostgreSQL and MongoDB instances
    # Update the connection configurations as needed for your environment
    
    asyncio.run(main())
