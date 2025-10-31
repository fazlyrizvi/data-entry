"""
Main module for Rollback and Recovery System

Provides unified interface for all recovery operations and demonstrates system usage.
"""
import asyncio
import json
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

import click
import structlog
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.panel import Panel

# Import our modules
from .transaction_manager import (
    get_transaction_manager, TransactionManager, IsolationLevel
)
from .backup_handler import get_backup_handler, BackupHandler, BackupType
from .recovery_orchestrator import (
    get_recovery_orchestrator, RecoveryOrchestrator, RecoveryType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = structlog.get_logger(__name__)
console = Console()


class RollbackRecoverySystem:
    """
    Unified rollback and recovery system orchestrator
    
    Provides a high-level interface for all recovery operations including:
    - Transaction management
    - Backup creation and restoration
    - Point-in-time recovery
    - Disaster recovery
    - Data consistency monitoring
    """

    def __init__(self,
                 backup_directory: str = "/var/backups",
                 enable_monitoring: bool = True,
                 max_concurrent_operations: int = 3):
        self.backup_directory = Path(backup_directory)
        self.enable_monitoring = enable_monitoring
        self.max_concurrent_operations = max_concurrent_operations
        
        # Initialize components
        self.transaction_manager: TransactionManager = get_transaction_manager()
        self.backup_handler: BackupHandler = get_backup_handler(
            base_backup_path=str(backup_directory)
        )
        self.recovery_orchestrator: RecoveryOrchestrator = get_recovery_orchestrator(
            max_concurrent_recoveries=max_concurrent_operations
        )
        
        # Background tasks
        self._background_tasks = []
        self._shutdown_event = asyncio.Event()
        
        # Statistics and monitoring
        self._start_time = time.time()
        self._statistics = {
            'operations_completed': 0,
            'recovery_operations': 0,
            'backups_created': 0,
            'data_restored_gb': 0.0
        }

    async def start(self):
        """Start the rollback recovery system"""
        console.print("[bold blue]Starting Rollback Recovery System...[/bold blue]")
        
        # Ensure backup directory exists
        self.backup_directory.mkdir(parents=True, exist_ok=True)
        
        # Start background monitoring tasks
        if self.enable_monitoring:
            self._start_background_tasks()
        
        console.print("[green]✓ System started successfully[/green]")
        self._log_system_startup()

    def _log_system_startup(self):
        """Log system startup information"""
        logger.info("Rollback Recovery System started",
                   backup_directory=str(self.backup_directory),
                   monitoring_enabled=self.enable_monitoring)

    def _start_background_tasks(self):
        """Start background monitoring and maintenance tasks"""
        self._background_tasks = [
            asyncio.create_task(self._periodic_health_check()),
            asyncio.create_task(self._periodic_backup_maintenance()),
            asyncio.create_task(self._periodic_statistics_collection())
        ]

    async def _periodic_health_check(self):
        """Periodic system health check"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Check component health
                health_status = await self._check_system_health()
                
                if not health_status['healthy']:
                    logger.warning("System health check failed", **health_status)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Health check error", error=str(e))

    async def _periodic_backup_maintenance(self):
        """Periodic backup maintenance"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(3600)  # Every hour
                
                # Apply retention policies
                retention_results = self.backup_handler.apply_retention_policy()
                
                logger.info("Backup maintenance completed", **retention_results)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Backup maintenance error", error=str(e))

    async def _periodic_statistics_collection(self):
        """Periodic statistics collection"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(1800)  # Every 30 minutes
                
                # Update statistics
                await self._update_statistics()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Statistics collection error", error=str(e))

    async def _check_system_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        health_status = {
            'healthy': True,
            'components': {},
            'issues': []
        }
        
        try:
            # Check transaction manager
            tm_stats = self.transaction_manager.get_statistics()
            health_status['components']['transaction_manager'] = {
                'healthy': True,
                'active_transactions': tm_stats['active_transactions'],
                'failed_rate': tm_stats.get('failed_transactions', 0) / max(tm_stats['total_transactions'], 1)
            }
            
        except Exception as e:
            health_status['components']['transaction_manager'] = {'healthy': False, 'error': str(e)}
            health_status['healthy'] = False
            health_status['issues'].append(f"Transaction Manager: {e}")
        
        try:
            # Check backup handler
            bh_stats = self.backup_handler.get_statistics()
            health_status['components']['backup_handler'] = {
                'healthy': True,
                'total_backups': bh_stats['total_backups'],
                'failed_backups': bh_stats['failed_backups']
            }
            
        except Exception as e:
            health_status['components']['backup_handler'] = {'healthy': False, 'error': str(e)}
            health_status['healthy'] = False
            health_status['issues'].append(f"Backup Handler: {e}")
        
        try:
            # Check recovery orchestrator
            ro_stats = self.recovery_orchestrator.get_statistics()
            health_status['components']['recovery_orchestrator'] = {
                'healthy': True,
                'active_recoveries': ro_stats['active_recoveries']
            }
            
        except Exception as e:
            health_status['components']['recovery_orchestrator'] = {'healthy': False, 'error': str(e)}
            health_status['healthy'] = False
            health_status['issues'].append(f"Recovery Orchestrator: {e}")
        
        return health_status

    async def _update_statistics(self):
        """Update system statistics"""
        try:
            tm_stats = self.transaction_manager.get_statistics()
            bh_stats = self.backup_handler.get_statistics()
            ro_stats = self.recovery_orchestrator.get_statistics()
            
            self._statistics.update({
                'uptime_seconds': time.time() - self._start_time,
                'total_transactions': tm_stats['total_transactions'],
                'total_backups': bh_stats['total_backups'],
                'total_recovery_operations': ro_stats['total_recovery_operations'],
                'system_health': 'healthy'
            })
            
        except Exception as e:
            logger.error("Statistics update failed", error=str(e))

    async def stop(self):
        """Stop the rollback recovery system"""
        console.print("[yellow]Stopping Rollback Recovery System...[/yellow]")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        console.print("[green]✓ System stopped successfully[/green]")

    # Transaction Management Methods

    async def execute_transactional_operation(self,
                                            operation_func,
                                            *args,
                                            isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED,
                                            **kwargs) -> Any:
        """
        Execute an operation within a transaction
        
        Args:
            operation_func: Function to execute
            *args: Arguments for operation function
            isolation_level: Transaction isolation level
            **kwargs: Keyword arguments for operation function
            
        Returns:
            Operation result
        """
        transaction_id = self.transaction_manager.begin_transaction(isolation_level)
        
        try:
            # Execute operation
            result = await operation_func(*args, transaction_id=transaction_id, **kwargs)
            
            # Commit transaction
            success = self.transaction_manager.commit_transaction(transaction_id)
            
            if not success:
                raise RuntimeError("Transaction commit failed")
            
            self._statistics['operations_completed'] += 1
            return result
            
        except Exception as e:
            # Rollback transaction
            self.transaction_manager.abort_transaction(transaction_id)
            logger.error("Transactional operation failed", error=str(e))
            raise

    async def rollback_transaction(self, transaction_id: UUID) -> bool:
        """Rollback a specific transaction"""
        return self.transaction_manager.abort_transaction(transaction_id)

    def get_transaction_status(self, transaction_id: UUID) -> Optional[Dict[str, Any]]:
        """Get transaction status"""
        return self.transaction_manager.get_transaction_status(transaction_id)

    # Backup Methods

    async def create_backup(self,
                          source_path: str,
                          backup_type: BackupType = BackupType.FULL,
                          description: Optional[str] = None,
                          tags: Optional[List[str]] = None) -> UUID:
        """
        Create a backup
        
        Args:
            source_path: Source path to backup
            backup_type: Type of backup
            description: Optional description
            tags: Optional tags
            
        Returns:
            Backup ID
        """
        with Progress() as progress:
            task = progress.add_task("[cyan]Creating backup...", total=1)
            
            backup_id = self.backup_handler.create_backup(
                source_path=source_path,
                backup_type=backup_type,
                description=description,
                tags=tags
            )
            
            progress.update(task, completed=1)
        
        self._statistics['backups_created'] += 1
        return backup_id

    async def restore_backup(self,
                           backup_id: UUID,
                           target_path: str,
                           validate: bool = True) -> bool:
        """
        Restore from backup
        
        Args:
            backup_id: Backup to restore
            target_path: Target location
            validate: Validate backup integrity
            
        Returns:
            True if restore successful
        """
        with Progress() as progress:
            task = progress.add_task("[cyan]Restoring backup...", total=1)
            
            success = await self.backup_handler.restore_backup(
                backup_id=backup_id,
                target_path=target_path,
                validate_checksum=validate
            )
            
            progress.update(task, completed=1)
        
        if success:
            # Estimate restored data size
            backup_info = self.backup_handler.get_backup_info(backup_id)
            if backup_info:
                self._statistics['data_restored_gb'] += backup_info.size_bytes / (1024**3)
        
        return success

    def list_backups(self,
                    backup_type: Optional[BackupType] = None,
                    status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available backups"""
        from .backup_handler import BackupStatus
        
        status_obj = None
        if status_filter:
            try:
                status_obj = BackupStatus(status_filter)
            except ValueError:
                pass
        
        backups = self.backup_handler.list_backups(
            backup_type=backup_type,
            status=status_obj
        )
        
        return [
            {
                'id': str(backup.backup_id),
                'type': backup.backup_type.value,
                'size_gb': backup.size_bytes / (1024**3),
                'compressed_size_gb': backup.compressed_size / (1024**3),
                'created_at': backup.created_at,
                'status': backup.status.value,
                'description': backup.description or ''
            }
            for backup in backups
        ]

    # Recovery Methods

    async def perform_point_in_time_recovery(self,
                                           target_timestamp: float,
                                           target_path: str,
                                           backup_selection: Optional[List[UUID]] = None) -> UUID:
        """
        Perform point-in-time recovery
        
        Args:
            target_timestamp: Point in time to recover to
            target_path: Target path for recovery
            backup_selection: Optional backup IDs to use
            
        Returns:
            Recovery plan ID
        """
        with Progress() as progress:
            task = progress.add_task("[cyan]Performing point-in-time recovery...", total=1)
            
            recovery_id = await self.recovery_orchestrator.initiate_recovery(
                recovery_type=RecoveryType.POINT_IN_TIME,
                target_timestamp=target_timestamp,
                source_backups=backup_selection,
                target_systems=['recovery_target'],
                recovery_options={
                    'target_path': target_path,
                    'conflict_resolution': 'overwrite'
                }
            )
            
            progress.update(task, completed=1)
        
        self._statistics['recovery_operations'] += 1
        return recovery_id

    async def perform_full_restore(self,
                                 source_backups: List[UUID],
                                 target_path: str) -> UUID:
        """
        Perform full restore from backups
        
        Args:
            source_backups: Backup IDs to restore from
            target_path: Target path for restore
            
        Returns:
            Recovery plan ID
        """
        with Progress() as progress:
            task = progress.add_task("[cyan]Performing full restore...", total=1)
            
            recovery_id = await self.recovery_orchestrator.initiate_recovery(
                recovery_type=RecoveryType.FULL_RESTORE,
                source_backups=source_backups,
                target_systems=['restore_target'],
                recovery_options={
                    'target_path': target_path,
                    'conflict_resolution': 'overwrite'
                }
            )
            
            progress.update(task, completed=1)
        
        self._statistics['recovery_operations'] += 1
        return recovery_id

    async def trigger_disaster_recovery(self, scenario: str) -> UUID:
        """Trigger disaster recovery procedure"""
        with Progress() as progress:
            task = progress.add_task("[red]Triggering disaster recovery...", total=1)
            
            recovery_id = await self.recovery_orchestrator.disaster_recovery_trigger(
                disaster_scenario=scenario
            )
            
            progress.update(task, completed=1)
        
        self._statistics['recovery_operations'] += 1
        return recovery_id

    # Monitoring and Status Methods

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            health = asyncio.create_task(self._check_system_health())
            
            return {
                'system': 'Rollback Recovery System',
                'status': 'running',
                'uptime_hours': (time.time() - self._start_time) / 3600,
                'statistics': self._statistics,
                'components': {
                    'transaction_manager': self.transaction_manager.get_statistics(),
                    'backup_handler': self.backup_handler.get_statistics(),
                    'recovery_orchestrator': self.recovery_orchestrator.get_statistics()
                },
                'health': health.result() if health.done() else 'checking'
            }
        except Exception as e:
            return {
                'system': 'Rollback Recovery System',
                'status': 'error',
                'error': str(e)
            }

    def display_status_dashboard(self):
        """Display system status dashboard"""
        status = self.get_system_status()
        
        # Create status table
        table = Table(title="Rollback Recovery System Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Metrics", style="yellow")
        
        # Transaction Manager
        tm_stats = status['components']['transaction_manager']
        table.add_row(
            "Transaction Manager",
            "✓ Running",
            f"{tm_stats['active_transactions']} active, "
            f"{tm_stats['total_transactions']} total"
        )
        
        # Backup Handler
        bh_stats = status['components']['backup_handler']
        table.add_row(
            "Backup Handler",
            "✓ Running",
            f"{bh_stats['total_backups']} backups, "
            f"{bh_stats['compression_ratio']:.1f}x ratio"
        )
        
        # Recovery Orchestrator
        ro_stats = status['components']['recovery_orchestrator']
        table.add_row(
            "Recovery Orchestrator",
            "✓ Running",
            f"{ro_stats['active_recoveries']} active recoveries"
        )
        
        console.print(table)
        
        # Display statistics
        stats_panel = Panel(
            f"Uptime: {status['uptime_hours']:.1f} hours\n"
            f"Operations: {self._statistics['operations_completed']}\n"
            f"Backups: {self._statistics['backups_created']}\n"
            f"Recovery Operations: {self._statistics['recovery_operations']}\n"
            f"Data Restored: {self._statistics['data_restored_gb']:.1f} GB",
            title="System Statistics"
        )
        console.print(stats_panel)

    def validate_data_consistency(self) -> Dict[str, Any]:
        """Validate data consistency across the system"""
        return self.recovery_orchestrator.get_consistency_report()

    # Utility Methods

    def cleanup_old_data(self, retention_days: int = 30):
        """Cleanup old system data"""
        # Clean up old transaction snapshots
        self.transaction_manager.cleanup_old_snapshots(retention_days)
        
        # Apply backup retention policies
        retention_results = self.backup_handler.apply_retention_policy()
        
        logger.info("System cleanup completed", **retention_results)
        return retention_results


# Global system instance
_system_instance: Optional[RollbackRecoverySystem] = None


def get_system(**kwargs) -> RollbackRecoverySystem:
    """Get or create global system instance"""
    global _system_instance
    if _system_instance is None:
        _system_instance = RollbackRecoverySystem(**kwargs)
    return _system_instance


# CLI Interface
@click.group()
@click.option('--backup-dir', default='/var/backups', help='Backup directory')
@click.option('--enable-monitoring/--disable-monitoring', default=True, 
              help='Enable system monitoring')
@click.pass_context
def cli(ctx, backup_dir, enable_monitoring):
    """Rollback and Recovery System CLI"""
    ctx.ensure_object(dict)
    ctx.obj['system'] = get_system(
        backup_directory=backup_dir,
        enable_monitoring=enable_monitoring
    )


@cli.command()
@click.pass_context
async def start(ctx):
    """Start the rollback recovery system"""
    system = ctx.obj['system']
    await system.start()
    
    # Display status dashboard
    system.display_status_dashboard()


@cli.command()
@click.pass_context
async def stop(ctx):
    """Stop the rollback recovery system"""
    system = ctx.obj['system']
    await system.stop()


@cli.command()
@click.pass_context
def status(ctx):
    """Display system status"""
    system = ctx.obj['system']
    system.display_status_dashboard()


@cli.command()
@click.argument('source_path')
@click.option('--type', 'backup_type', default='full', 
              type=click.Choice(['full', 'incremental', 'differential']),
              help='Backup type')
@click.option('--description', help='Backup description')
@click.option('--tags', multiple=True, help='Backup tags')
@click.pass_context
async def backup(ctx, source_path, backup_type, description, tags):
    """Create a backup"""
    system = ctx.obj['system']
    
    backup_type_enum = {
        'full': BackupType.FULL,
        'incremental': BackupType.INCREMENTAL,
        'differential': BackupType.DIFFERENTIAL
    }[backup_type]
    
    backup_id = await system.create_backup(
        source_path=source_path,
        backup_type=backup_type_enum,
        description=description,
        tags=list(tags)
    )
    
    console.print(f"[green]Backup created: {backup_id}[/green]")


@cli.command()
@click.argument('backup_id')
@click.argument('target_path')
@click.option('--validate/--no-validate', default=True, help='Validate backup integrity')
@click.pass_context
async def restore(ctx, backup_id, target_path, validate):
    """Restore from backup"""
    system = ctx.obj['system']
    
    try:
        backup_uuid = UUID(backup_id)
        success = await system.restore_backup(backup_uuid, target_path, validate)
        
        if success:
            console.print(f"[green]Restore completed: {target_path}[/green]")
        else:
            console.print("[red]Restore failed[/red]")
    except ValueError:
        console.print(f"[red]Invalid backup ID: {backup_id}[/red]")


@cli.command()
@click.pass_context
def list_backups(ctx):
    """List available backups"""
    system = ctx.obj['system']
    backups = system.list_backups()
    
    if not backups:
        console.print("No backups found")
        return
    
    table = Table(title="Available Backups")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Size", style="yellow")
    table.add_column("Status", style="green")
    table.add_column("Created", style="blue")
    table.add_column("Description", style="white")
    
    for backup in backups:
        table.add_row(
            backup['id'][:8] + "...",
            backup['type'],
            f"{backup['size_gb']:.1f} GB",
            backup['status'],
            f"{time.ctime(backup['created_at'])[:19]}",
            backup['description'][:30]
        )
    
    console.print(table)


@cli.command()
@click.argument('target_timestamp', type=float)
@click.argument('target_path')
@click.pass_context
async def point_in_time_recovery(ctx, target_timestamp, target_path):
    """Perform point-in-time recovery"""
    system = ctx.obj['system']
    
    recovery_id = await system.perform_point_in_time_recovery(
        target_timestamp=target_timestamp,
        target_path=target_path
    )
    
    console.print(f"[green]Point-in-time recovery initiated: {recovery_id}[/green]")


# Main entry point
async def main():
    """Main entry point for the rollback recovery system"""
    if len(sys.argv) > 1:
        # CLI mode
        cli()
    else:
        # Server mode
        system = get_system()
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            console.print("\n[yellow]Shutting down...[/yellow]")
            asyncio.create_task(system.stop())
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start system
        await system.start()
        
        try:
            # Keep running
            await system._shutdown_event.wait()
        except KeyboardInterrupt:
            pass
        finally:
            await system.stop()


if __name__ == "__main__":
    asyncio.run(main())
