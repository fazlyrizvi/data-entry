#!/usr/bin/env python3
"""
Example usage of the Rollback Recovery System

This script demonstrates various features of the rollback recovery system
including transaction management, backup/restore, and recovery operations.
"""

import asyncio
import time
from pathlib import Path

# Import the rollback recovery system
from rollback_recovery import (
    get_system,
    IsolationLevel,
    BackupType,
    RecoveryType
)


async def example_transactional_operation():
    """Demonstrate transactional operations"""
    print("\n" + "="*60)
    print("EXAMPLE: Transactional Operations")
    print("="*60)
    
    system = get_system()
    
    # Example data
    order_data = {
        "order_id": 12345,
        "customer_id": 67890,
        "product_id": "PROD-001",
        "quantity": 2,
        "price": 29.99
    }
    
    print(f"\n1. Executing transactional operation...")
    print(f"   Order data: {order_data}")
    
    try:
        # Execute operation within transaction
        result = await system.execute_transactional_operation(
            operation_func=process_order,
            order_data=order_data,
            isolation_level=IsolationLevel.SERIALIZABLE
        )
        
        print(f"\n2. Transaction committed successfully!")
        print(f"   Result: {result}")
        
    except Exception as e:
        print(f"\n2. Transaction failed: {e}")
    
    # Show transaction status
    print(f"\n3. Transaction Statistics:")
    tm_stats = system.transaction_manager.get_statistics()
    print(f"   Total transactions: {tm_stats['total_transactions']}")
    print(f"   Committed: {tm_stats['committed_transactions']}")
    print(f"   Aborted: {tm_stats['aborted_transactions']}")


async def process_order(order_data, transaction_id=None):
    """Simulated order processing function"""
    # In a real scenario, this would interact with actual databases
    # For this example, we'll just simulate the operations
    
    print(f"   - Recording order creation...")
    print(f"   - Updating inventory...")
    print(f"   - Creating audit log entry...")
    
    # Simulate some processing time
    await asyncio.sleep(0.1)
    
    return {"status": "processed", "order_id": order_data["order_id"]}


async def example_backup_and_restore():
    """Demonstrate backup and restore operations"""
    print("\n" + "="*60)
    print("EXAMPLE: Backup and Restore Operations")
    print("="*60)
    
    system = get_system()
    
    # Create example data to backup
    example_data_path = Path("/tmp/example_data")
    example_data_path.mkdir(exist_ok=True)
    
    # Create some example files
    for i in range(5):
        file_path = example_data_path / f"file_{i}.txt"
        file_path.write_text(f"Example data file {i}\n" * 100)
    
    print(f"\n1. Created example data at: {example_data_path}")
    print(f"   Files: {len(list(example_data_path.glob('*')))}")
    
    # Create backup
    print(f"\n2. Creating full backup...")
    backup_id = await system.create_backup(
        source_path=str(example_data_path),
        backup_type=BackupType.FULL,
        description="Example backup for testing",
        tags=["example", "test", "demo"]
    )
    
    print(f"   Backup created: {backup_id}")
    
    # List backups
    print(f"\n3. Listing available backups...")
    backups = system.list_backups()
    
    for backup in backups[:3]:  # Show first 3 backups
        print(f"   - {backup['id'][:8]}... | "
              f"Type: {backup['type']} | "
              f"Size: {backup['size_gb']:.2f}GB | "
              f"Status: {backup['status']}")
    
    # Restore backup
    restore_path = Path("/tmp/restored_data")
    print(f"\n4. Restoring backup to: {restore_path}")
    
    success = await system.restore_backup(
        backup_id=backup_id,
        target_path=str(restore_path),
        validate=True
    )
    
    if success:
        print(f"   Restore completed successfully!")
        restored_files = len(list(restore_path.glob('*')))
        print(f"   Restored files: {restored_files}")
    else:
        print(f"   Restore failed!")
    
    # Show backup statistics
    print(f"\n5. Backup Statistics:")
    bh_stats = system.backup_handler.get_statistics()
    print(f"   Total backups: {bh_stats['total_backups']}")
    print(f"   Completed: {bh_stats['completed_backups']}")
    print(f"   Failed: {bh_stats['failed_backups']}")
    print(f"   Compression ratio: {bh_stats['compression_ratio']:.2f}x")


async def example_point_in_time_recovery():
    """Demonstrate point-in-time recovery"""
    print("\n" + "="*60)
    print("EXAMPLE: Point-in-Time Recovery")
    print("="*60)
    
    system = get_system()
    
    # Calculate target timestamp (1 hour ago)
    target_timestamp = time.time() - 3600
    
    print(f"\n1. Initiating point-in-time recovery...")
    print(f"   Target timestamp: {time.ctime(target_timestamp)}")
    print(f"   Current time: {time.ctime()}")
    
    recovery_path = Path("/tmp/point_in_time_recovery")
    print(f"   Recovery target: {recovery_path}")
    
    try:
        # Find available backups for point-in-time recovery
        print(f"\n2. Searching for appropriate backups...")
        recent_backups = system.backup_handler.list_backups()
        
        if recent_backups:
            # Use most recent backup as base
            backup_id = recent_backups[0].id
            print(f"   Using backup: {backup_id}")
            
            # Perform recovery
            recovery_id = await system.perform_point_in_time_recovery(
                target_timestamp=target_timestamp,
                target_path=str(recovery_path),
                backup_selection=[backup_id]
            )
            
            print(f"\n3. Recovery initiated: {recovery_id}")
            print(f"   Monitor recovery status in the system status")
            
        else:
            print(f"   No backups available for recovery")
            
    except Exception as e:
        print(f"   Recovery failed: {e}")


async def example_system_monitoring():
    """Demonstrate system monitoring and status"""
    print("\n" + "="*60)
    print("EXAMPLE: System Monitoring and Status")
    print("="*60)
    
    system = get_system()
    
    print(f"\n1. Getting comprehensive system status...")
    status = system.get_system_status()
    
    print(f"   System: {status['system']}")
    print(f"   Status: {status['status']}")
    print(f"   Uptime: {status['uptime_hours']:.2f} hours")
    
    print(f"\n2. Component Status:")
    components = status['components']
    
    print(f"   Transaction Manager:")
    tm_stats = components['transaction_manager']
    print(f"     - Active transactions: {tm_stats['active_transactions']}")
    print(f"     - Total operations: {tm_stats['total_transactions']}")
    
    print(f"   Backup Handler:")
    bh_stats = components['backup_handler']
    print(f"     - Total backups: {bh_stats['total_backups']}")
    print(f"     - Compression ratio: {bh_stats['compression_ratio']:.2f}x")
    
    print(f"   Recovery Orchestrator:")
    ro_stats = components['recovery_orchestrator']
    print(f"     - Active recoveries: {ro_stats['active_recoveries']}")
    print(f"     - Total recovery operations: {ro_stats['total_recovery_operations']}")
    
    print(f"\n3. Data Consistency Check:")
    consistency_report = system.validate_data_consistency()
    print(f"   Total checks: {consistency_report['total_checks']}")
    print(f"   Passed: {consistency_report['passed_checks']}")
    print(f"   Success rate: {consistency_report['success_rate']*100:.1f}%")


async def example_consistency_validation():
    """Demonstrate data consistency validation"""
    print("\n" + "="*60)
    print("EXAMPLE: Data Consistency Validation")
    print("="*60)
    
    system = get_system()
    
    print(f"\n1. Running comprehensive consistency checks...")
    consistency_report = system.validate_data_consistency()
    
    print(f"\n2. Consistency Report Summary:")
    print(f"   Total checks performed: {consistency_report['total_checks']}")
    print(f"   Checks passed: {consistency_report['passed_checks']}")
    print(f"   Checks failed: {consistency_report['failed_checks']}")
    print(f"   Overall success rate: {consistency_report['success_rate']*100:.1f}%")
    
    if consistency_report['recent_checks']:
        print(f"\n3. Recent Check Details:")
        for check in consistency_report['recent_checks'][:3]:
            status = "✓" if check['passed'] else "✗"
            print(f"   {status} {check['check_type']} - "
                  f"{check['table_name']} - "
                  f"{check['violations']} violations")


async def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("ROLLBACK RECOVERY SYSTEM - USAGE EXAMPLES")
    print("="*60)
    print("\nThis script demonstrates the key features of the")
    print("rollback recovery system including:")
    print("- Transaction management with ACID compliance")
    print("- Backup and restore operations")
    print("- Point-in-time recovery")
    print("- System monitoring and status")
    print("- Data consistency validation")
    
    # Initialize system
    print("\n" + "-"*60)
    print("Initializing Rollback Recovery System...")
    
    system = get_system(
        backup_directory="/tmp/rollback_recovery_backups",
        enable_monitoring=True,
        max_concurrent_operations=3
    )
    
    await system.start()
    print("System initialized and started successfully!")
    
    try:
        # Run examples
        await example_transactional_operation()
        await example_backup_and_restore()
        await example_point_in_time_recovery()
        await example_system_monitoring()
        await example_consistency_validation()
        
        print("\n" + "="*60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    finally:
        # Cleanup
        print("\n" + "-"*60)
        print("Shutting down system...")
        await system.stop()
        print("System shutdown complete.")


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
