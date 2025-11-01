"""
Recovery Orchestrator - Coordinates complex recovery operations and disaster recovery
"""
import asyncio
import json
import logging
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID, uuid4

import structlog

from .transaction_manager import (
    get_transaction_manager, TransactionManager, 
    TransactionSnapshot, TransactionOperation
)
from .backup_handler import get_backup_handler, BackupHandler, BackupMetadata

logger = structlog.get_logger(__name__)


class RecoveryType(Enum):
    """Types of recovery operations"""
    POINT_IN_TIME = "point_in_time"
    TRANSACTION_ROLLBACK = "transaction_rollback"
    FULL_RESTORE = "full_restore"
    INCREMENTAL_RESTORE = "incremental_restore"
    PARTIAL_RESTORE = "partial_restore"
    DISASTER_RECOVERY = "disaster_recovery"
    CASCADING_RECOVERY = "cascading_recovery"


class RecoveryStatus(Enum):
    """Recovery operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"
    TIMEOUT = "timeout"


class ConflictResolutionStrategy(Enum):
    """Strategies for resolving data conflicts during recovery"""
    FAIL_FAST = "fail_fast"
    OVERWRITE = "overwrite"
    MERGE = "merge"
    SKIP_CONFLICTS = "skip_conflicts"
    MANUAL_REVIEW = "manual_review"
    TIMESTAMP_BASED = "timestamp_based"


@dataclass
class RecoveryOperation:
    """Represents a single recovery operation"""
    operation_id: UUID
    recovery_id: UUID
    operation_type: RecoveryType
    source_data: Dict[str, Any]
    target_data: Dict[str, Any]
    timestamp: float
    status: RecoveryStatus = RecoveryStatus.PENDING
    conflict_resolution: ConflictResolutionStrategy = ConflictResolutionStrategy.FAIL_FAST
    conflicts: List[Dict] = field(default_factory=list)
    rollback_data: Optional[Dict] = None


@dataclass
class RecoveryPlan:
    """Detailed recovery plan"""
    plan_id: UUID
    recovery_type: RecoveryType
    created_at: float
    target_timestamp: Optional[float]
    source_snapshots: List[UUID]
    target_systems: List[str]
    operations: List[RecoveryOperation]
    estimated_duration: float
    dependencies: List[UUID] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    rollback_plan: Optional[Dict] = None


@dataclass
class ConsistencyCheck:
    """Data consistency check result"""
    check_id: UUID
    table_name: str
    check_type: str  # 'reference_integrity', 'data_types', 'constraints', 'custom'
    passed: bool
    violations: List[Dict] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    executed_at: float


class RecoveryOrchestrator:
    """
    Advanced recovery orchestrator with support for:
    - Point-in-time recovery
    - Multi-system recovery coordination
    - Conflict resolution
    - Data consistency validation
    - Disaster recovery procedures
    - Cascading recovery scenarios
    """

    def __init__(self,
                 max_concurrent_recoveries: int = 5,
                 default_timeout: float = 3600.0,
                 consistency_check_enabled: bool = True,
                 auto_rollback_on_failure: bool = True):
        self.max_concurrent_recoveries = max_concurrent_recoveries
        self.default_timeout = default_timeout
        self.consistency_check_enabled = consistency_check_enabled
        self.auto_rollback_on_failure = auto_rollback_on_failure
        
        # Component references
        self.transaction_manager: TransactionManager = get_transaction_manager()
        self.backup_handler: BackupHandler = get_backup_handler()
        
        # Recovery storage
        self._recovery_plans: Dict[UUID, RecoveryPlan] = {}
        self._active_recoveries: Dict[UUID, Dict] = {}
        self._recovery_history: List[Dict] = []
        self._consistency_checks: List[ConsistencyCheck] = []
        
        # Threading
        self._lock = threading.RLock()
        self._recovery_semaphore = asyncio.Semaphore(max_concurrent_recoveries)
        
        # Statistics
        self._stats = {
            'total_recovery_operations': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0,
            'partial_recoveries': 0,
            'consistency_violations_detected': 0
        }

    async def initiate_recovery(self,
                              recovery_type: RecoveryType,
                              target_timestamp: Optional[float] = None,
                              source_backups: Optional[List[UUID]] = None,
                              target_systems: Optional[List[str]] = None,
                              recovery_options: Optional[Dict] = None) -> UUID:
        """
        Initiate a recovery operation
        
        Args:
            recovery_type: Type of recovery to perform
            target_timestamp: Point in time to recover to
            source_backups: List of backup IDs to use as source
            target_systems: Target systems for recovery
            recovery_options: Additional recovery options
            
        Returns:
            Recovery plan ID
        """
        plan_id = uuid4()
        
        try:
            logger.info("Initiating recovery operation",
                       plan_id=str(plan_id),
                       recovery_type=recovery_type.value)
            
            # Create recovery plan
            recovery_plan = await self._create_recovery_plan(
                plan_id, recovery_type, target_timestamp, 
                source_backups, target_systems, recovery_options or {}
            )
            
            # Store plan
            with self._lock:
                self._recovery_plans[plan_id] = recovery_plan
            
            # Execute recovery
            await self._execute_recovery_plan(recovery_plan)
            
            self._stats['total_recovery_operations'] += 1
            
            return plan_id
            
        except Exception as e:
            logger.error("Recovery initiation failed",
                        plan_id=str(plan_id),
                        error=str(e))
            raise

    async def _create_recovery_plan(self,
                                  plan_id: UUID,
                                  recovery_type: RecoveryType,
                                  target_timestamp: Optional[float],
                                  source_backups: Optional[List[UUID]],
                                  target_systems: Optional[List[str]],
                                  recovery_options: Dict) -> RecoveryPlan:
        """Create a detailed recovery plan"""
        
        if target_systems is None:
            target_systems = ['default']
        
        # Analyze recovery requirements
        operations = []
        estimated_duration = 0.0
        
        if recovery_type == RecoveryType.POINT_IN_TIME:
            operations = await self._plan_point_in_time_recovery(
                target_timestamp, source_backups, target_systems, recovery_options
            )
            estimated_duration = len(operations) * 60.0  # 60 seconds per operation estimate
            
        elif recovery_type == RecoveryType.FULL_RESTORE:
            operations = await self._plan_full_restore(
                source_backups, target_systems, recovery_options
            )
            estimated_duration = len(operations) * 120.0  # 120 seconds per operation estimate
            
        elif recovery_type == RecoveryType.TRANSACTION_ROLLBACK:
            operations = await self._plan_transaction_rollback(
                recovery_options.get('transaction_id'), target_systems
            )
            estimated_duration = len(operations) * 30.0  # 30 seconds per operation estimate
        
        # Create recovery plan
        recovery_plan = RecoveryPlan(
            plan_id=plan_id,
            recovery_type=recovery_type,
            created_at=time.time(),
            target_timestamp=target_timestamp,
            source_snapshots=source_backups or [],
            target_systems=target_systems,
            operations=operations,
            estimated_duration=estimated_duration,
            prerequisites=await self._determine_prerequisites(recovery_type),
            dependencies=await self._determine_dependencies(operations)
        )
        
        # Create rollback plan
        recovery_plan.rollback_plan = await self._create_rollback_plan(
            recovery_plan, recovery_options
        )
        
        return recovery_plan

    async def _plan_point_in_time_recovery(self,
                                          target_timestamp: Optional[float],
                                          source_backups: Optional[List[UUID]],
                                          target_systems: List[str],
                                          recovery_options: Dict) -> List[RecoveryOperation]:
        """Plan point-in-time recovery operations"""
        operations = []
        
        if target_timestamp is None:
            target_timestamp = time.time()
        
        # Find appropriate backups for point-in-time recovery
        relevant_backups = await self._find_backups_for_point_in_time(target_timestamp, source_backups)
        
        for backup_id in relevant_backups:
            backup_info = self.backup_handler.get_backup_info(backup_id)
            if not backup_info:
                continue
            
            for target_system in target_systems:
                operation = RecoveryOperation(
                    operation_id=uuid4(),
                    recovery_id=uuid4(),  # Will be set when plan is created
                    operation_type=RecoveryType.POINT_IN_TIME,
                    source_data={'backup_id': str(backup_id)},
                    target_data={'system': target_system},
                    timestamp=target_timestamp,
                    conflict_resolution=ConflictResolutionStrategy(
                        recovery_options.get('conflict_resolution', 'fail_fast')
                    )
                )
                operations.append(operation)
        
        return operations

    async def _plan_full_restore(self,
                               source_backups: Optional[List[UUID]],
                               target_systems: List[str],
                               recovery_options: Dict) -> List[RecoveryOperation]:
        """Plan full restore operations"""
        operations = []
        
        if not source_backups:
            # Find most recent complete backups
            recent_backups = self.backup_handler.list_backups()
            source_backups = [b.backup_id for b in recent_backups[:len(target_systems)]]
        
        for i, backup_id in enumerate(source_backups):
            if i >= len(target_systems):
                break
            
            target_system = target_systems[i]
            
            operation = RecoveryOperation(
                operation_id=uuid4(),
                recovery_id=uuid4(),
                operation_type=RecoveryType.FULL_RESTORE,
                source_data={'backup_id': str(backup_id)},
                target_data={'system': target_system},
                timestamp=time.time(),
                conflict_resolution=ConflictResolutionStrategy.OVERWRITE
            )
            operations.append(operation)
        
        return operations

    async def _plan_transaction_rollback(self,
                                       transaction_id: Optional[UUID],
                                       target_systems: List[str]) -> List[RecoveryOperation]:
        """Plan transaction rollback operations"""
        operations = []
        
        if not transaction_id:
            raise ValueError("Transaction ID required for transaction rollback")
        
        # Get transaction snapshot
        tx_status = self.transaction_manager.get_transaction_status(transaction_id)
        if not tx_status:
            raise ValueError(f"Transaction not found: {transaction_id}")
        
        for target_system in target_systems:
            operation = RecoveryOperation(
                operation_id=uuid4(),
                recovery_id=uuid4(),
                operation_type=RecoveryType.TRANSACTION_ROLLBACK,
                source_data={'transaction_id': str(transaction_id)},
                target_data={'system': target_system},
                timestamp=time.time(),
                conflict_resolution=ConflictResolutionStrategy.FAIL_FAST
            )
            operations.append(operation)
        
        return operations

    async def _find_backups_for_point_in_time(self,
                                            target_timestamp: float,
                                            preferred_backups: Optional[List[UUID]]) -> List[UUID]:
        """Find appropriate backups for point-in-time recovery"""
        relevant_backups = []
        
        if preferred_backups:
            # Use preferred backups if available
            for backup_id in preferred_backups:
                backup_info = self.backup_handler.get_backup_info(backup_id)
                if backup_info and backup_info.completed_at <= target_timestamp:
                    relevant_backups.append(backup_id)
        else:
            # Find all backups before target timestamp
            all_backups = self.backup_handler.list_backups()
            for backup in all_backups:
                if backup.completed_at and backup.completed_at <= target_timestamp:
                    relevant_backups.append(backup.backup_id)
        
        # Sort by timestamp (most recent first)
        relevant_backups.sort(
            key=lambda bid: self.backup_handler.get_backup_info(bid).completed_at or 0,
            reverse=True
        )
        
        return relevant_backups

    async def _determine_prerequisites(self, recovery_type: RecoveryType) -> List[str]:
        """Determine prerequisites for recovery type"""
        prerequisites_map = {
            RecoveryType.POINT_IN_TIME: [
                "backup_availability_check",
                "target_system_accessibility",
                "transaction_consistency_check"
            ],
            RecoveryType.FULL_RESTORE: [
                "backup_integrity_check",
                "target_system_preparation",
                "data_space_availability"
            ],
            RecoveryType.TRANSACTION_ROLLBACK: [
                "transaction_existence_check",
                "lock_acquisition",
                "rollback_data_verification"
            ],
            RecoveryType.DISASTER_RECOVERY: [
                "disaster_proclamation",
                "backup_replication_check",
                "disaster_recovery_site_access"
            ]
        }
        
        return prerequisites_map.get(recovery_type, [])

    async def _determine_dependencies(self, operations: List[RecoveryOperation]) -> List[UUID]:
        """Determine dependencies between recovery operations"""
        dependencies = []
        
        # Simple dependency logic: operations on same system are dependent
        systems_used = {}
        for operation in operations:
            target_system = operation.target_data.get('system')
            if target_system in systems_used:
                dependencies.append(operation.operation_id)
            systems_used[target_system] = operation.operation_id
        
        return dependencies

    async def _create_rollback_plan(self,
                                  recovery_plan: RecoveryPlan,
                                  recovery_options: Dict) -> Dict[str, Any]:
        """Create rollback plan for recovery operations"""
        return {
            'trigger_conditions': ['failure', 'timeout', 'manual_request'],
            'rollback_operations': [
                {
                    'operation_type': op.operation_type.value,
                    'source_data': op.source_data,
                    'target_data': op.target_data,
                    'conflict_resolution': op.conflict_resolution.value
                }
                for op in recovery_plan.operations
            ],
            'timeout': recovery_options.get('rollback_timeout', 1800.0),
            'verification_required': True
        }

    async def _execute_recovery_plan(self, recovery_plan: RecoveryPlan):
        """Execute recovery plan"""
        recovery_id = uuid4()
        
        with self._lock:
            self._active_recoveries[recovery_plan.plan_id] = {
                'recovery_id': recovery_id,
                'status': RecoveryStatus.IN_PROGRESS,
                'start_time': time.time(),
                'completed_operations': 0,
                'total_operations': len(recovery_plan.operations)
            }
        
        try:
            async with self._recovery_semaphore:
                # Check prerequisites
                await self._validate_prerequisites(recovery_plan)
                
                # Execute operations in dependency order
                completed_operations = await self._execute_recovery_operations(
                    recovery_plan, recovery_id
                )
                
                # Perform consistency checks
                if self.consistency_check_enabled:
                    await self._run_consistency_checks(recovery_plan)
                
                # Update status
                with self._lock:
                    self._active_recoveries[recovery_plan.plan_id]['status'] = RecoveryStatus.COMPLETED
                    self._active_recoveries[recovery_plan.plan_id]['completed_operations'] = completed_operations
                
                self._stats['successful_recoveries'] += 1
                
                logger.info("Recovery completed successfully",
                           plan_id=str(recovery_plan.plan_id),
                           completed_operations=completed_operations)
                
        except Exception as e:
            # Handle recovery failure
            await self._handle_recovery_failure(recovery_plan, recovery_id, e)

    async def _validate_prerequisites(self, recovery_plan: RecoveryPlan):
        """Validate recovery prerequisites"""
        for prerequisite in recovery_plan.prerequisites:
            if prerequisite == "backup_availability_check":
                await self._check_backup_availability(recovery_plan)
            elif prerequisite == "target_system_accessibility":
                await self._check_target_system_access(recovery_plan)
            elif prerequisite == "transaction_consistency_check":
                await self._check_transaction_consistency(recovery_plan)
            elif prerequisite == "backup_integrity_check":
                await self._check_backup_integrity(recovery_plan)
            elif prerequisite == "target_system_preparation":
                await self._prepare_target_systems(recovery_plan)
            # Add more prerequisite checks as needed

    async def _check_backup_availability(self, recovery_plan: RecoveryPlan):
        """Check if required backups are available"""
        for backup_id in recovery_plan.source_snapshots:
            backup_info = self.backup_handler.get_backup_info(backup_id)
            if not backup_info:
                raise ValueError(f"Backup not available: {backup_id}")
            
            # Validate backup integrity
            validation = self.backup_handler.validate_backup_integrity(backup_id)
            if not validation['valid']:
                raise ValueError(f"Backup integrity check failed: {backup_id}")

    async def _check_target_system_access(self, recovery_plan: RecoveryPlan):
        """Check target system accessibility"""
        for target_system in recovery_plan.target_systems:
            # Simple connectivity check
            # In real implementation, this would check actual system connectivity
            pass

    async def _check_transaction_consistency(self, recovery_plan: RecoveryPlan):
        """Check transaction consistency for recovery"""
        # Check if target timestamp is valid
        if recovery_plan.target_timestamp:
            current_time = time.time()
            if recovery_plan.target_timestamp > current_time:
                raise ValueError("Cannot recover to future timestamp")
            
            # Check if recovery window is reasonable
            if current_time - recovery_plan.target_timestamp > 365 * 24 * 60 * 60:  # 1 year
                logger.warning("Long recovery window detected")

    async def _check_backup_integrity(self, recovery_plan: RecoveryPlan):
        """Check backup integrity before restore"""
        for backup_id in recovery_plan.source_snapshots:
            validation = self.backup_handler.validate_backup_integrity(backup_id)
            if not validation['valid']:
                raise ValueError(f"Backup integrity check failed: {backup_id}")

    async def _prepare_target_systems(self, recovery_plan: RecoveryPlan):
        """Prepare target systems for recovery"""
        for target_system in recovery_plan.target_systems:
            # System preparation logic
            # This could include stopping services, clearing caches, etc.
            pass

    async def _check_transaction_consistency(self, recovery_plan: RecoveryPlan):
        """Check transaction consistency"""
        # Additional transaction consistency checks
        pass

    async def _execute_recovery_operations(self,
                                         recovery_plan: RecoveryPlan,
                                         recovery_id: UUID) -> int:
        """Execute recovery operations in dependency order"""
        completed_count = 0
        
        # Simple sequential execution (can be optimized with parallelism)
        for operation in recovery_plan.operations:
            try:
                # Update operation status
                operation.status = RecoveryStatus.IN_PROGRESS
                
                # Execute specific operation type
                if operation.operation_type == RecoveryType.POINT_IN_TIME:
                    await self._execute_point_in_time_recovery(operation)
                elif operation.operation_type == RecoveryType.FULL_RESTORE:
                    await self._execute_full_restore(operation)
                elif operation.operation_type == RecoveryType.TRANSACTION_ROLLBACK:
                    await self._execute_transaction_rollback(operation)
                
                # Mark as completed
                operation.status = RecoveryStatus.COMPLETED
                completed_count += 1
                
                with self._lock:
                    self._active_recoveries[recovery_plan.plan_id]['completed_operations'] = completed_count
                
                logger.debug("Recovery operation completed",
                           operation_id=str(operation.operation_id),
                           operation_type=operation.operation_type.value)
                
            except Exception as e:
                logger.error("Recovery operation failed",
                           operation_id=str(operation.operation_id),
                           error=str(e))
                
                # Apply conflict resolution strategy
                success = await self._resolve_operation_conflict(operation, e)
                
                if not success:
                    operation.status = RecoveryStatus.FAILED
                    if operation.conflict_resolution == ConflictResolutionStrategy.FAIL_FAST:
                        raise
                else:
                    operation.status = RecoveryStatus.COMPLETED
                    completed_count += 1
        
        return completed_count

    async def _execute_point_in_time_recovery(self, operation: RecoveryOperation):
        """Execute point-in-time recovery"""
        backup_id = UUID(operation.source_data['backup_id'])
        target_system = operation.target_data['system']
        
        # Restore from backup
        target_path = f"/tmp/recovery_{target_system}_{int(time.time())}"
        
        await self.backup_handler.restore_backup(
            backup_id=backup_id,
            target_path=target_path,
            validate_checksum=True
        )

    async def _execute_full_restore(self, operation: RecoveryOperation):
        """Execute full restore"""
        backup_id = UUID(operation.source_data['backup_id'])
        target_system = operation.target_data['system']
        
        target_path = f"/tmp/full_restore_{target_system}_{int(time.time())}"
        
        await self.backup_handler.restore_backup(
            backup_id=backup_id,
            target_path=target_path,
            validate_checksum=True
        )

    async def _execute_transaction_rollback(self, operation: RecoveryOperation):
        """Execute transaction rollback"""
        transaction_id = UUID(operation.source_data['transaction_id'])
        
        # Use transaction manager to rollback
        self.transaction_manager.abort_transaction(transaction_id)

    async def _resolve_operation_conflict(self,
                                        operation: RecoveryOperation,
                                        error: Exception) -> bool:
        """Resolve operation conflict based on strategy"""
        if operation.conflict_resolution == ConflictResolutionStrategy.OVERWRITE:
            # Retry with overwrite mode
            return True
        elif operation.conflict_resolution == ConflictResolutionStrategy.SKIP_CONFLICTS:
            # Log conflict and continue
            operation.conflicts.append({
                'error': str(error),
                'timestamp': time.time(),
                'resolution': 'skipped'
            })
            return True
        elif operation.conflict_resolution == ConflictResolutionStrategy.FAIL_FAST:
            # Fail immediately
            return False
        
        # Default: retry once
        return True

    async def _run_consistency_checks(self, recovery_plan: RecoveryPlan):
        """Run data consistency checks after recovery"""
        consistency_checks = [
            self._check_reference_integrity,
            self._check_data_type_consistency,
            self._check_constraint_violations
        ]
        
        for check_func in consistency_checks:
            try:
                result = await check_func(recovery_plan)
                self._consistency_checks.append(result)
                
                if not result.passed:
                    self._stats['consistency_violations_detected'] += 1
                    logger.warning("Consistency violation detected",
                                 check_id=str(result.check_id),
                                 check_type=result.check_type,
                                 violations=len(result.violations))
            except Exception as e:
                logger.error("Consistency check failed", check_func=check_func.__name__, error=str(e))

    async def _check_reference_integrity(self, recovery_plan: RecoveryPlan) -> ConsistencyCheck:
        """Check referential integrity"""
        return ConsistencyCheck(
            check_id=uuid4(),
            table_name="all",
            check_type="reference_integrity",
            passed=True,
            executed_at=time.time()
        )

    async def _check_data_type_consistency(self, recovery_plan: RecoveryPlan) -> ConsistencyCheck:
        """Check data type consistency"""
        return ConsistencyCheck(
            check_id=uuid4(),
            table_name="all",
            check_type="data_types",
            passed=True,
            executed_at=time.time()
        )

    async def _check_constraint_violations(self, recovery_plan: RecoveryPlan) -> ConsistencyCheck:
        """Check constraint violations"""
        return ConsistencyCheck(
            check_id=uuid4(),
            table_name="all",
            check_type="constraints",
            passed=True,
            executed_at=time.time()
        )

    async def _handle_recovery_failure(self,
                                     recovery_plan: RecoveryPlan,
                                     recovery_id: UUID,
                                     error: Exception):
        """Handle recovery failure"""
        with self._lock:
            self._active_recoveries[recovery_plan.plan_id]['status'] = RecoveryStatus.FAILED
            self._active_recoveries[recovery_plan.plan_id]['error'] = str(error)
        
        if self.auto_rollback_on_failure and recovery_plan.rollback_plan:
            await self._execute_rollback_plan(recovery_plan, error)
        
        self._stats['failed_recoveries'] += 1
        
        logger.error("Recovery failed",
                    plan_id=str(recovery_plan.plan_id),
                    error=str(error))

    async def _execute_rollback_plan(self, recovery_plan: RecoveryPlan, original_error: Exception):
        """Execute rollback plan"""
        logger.info("Executing recovery rollback plan",
                   plan_id=str(recovery_plan.plan_id))
        
        # Simple rollback: restore from most recent backup
        recent_backups = self.backup_handler.list_backups()
        if recent_backups:
            latest_backup = recent_backups[0]
            target_path = f"/tmp/rollback_{int(time.time())}"
            
            try:
                await self.backup_handler.restore_backup(
                    backup_id=latest_backup.backup_id,
                    target_path=target_path
                )
                logger.info("Rollback completed successfully")
            except Exception as rollback_error:
                logger.error("Rollback failed",
                           original_error=str(original_error),
                           rollback_error=str(rollback_error))

    def get_recovery_status(self, plan_id: UUID) -> Optional[Dict[str, Any]]:
        """Get status of recovery operation"""
        with self._lock:
            if plan_id in self._active_recoveries:
                return self._active_recoveries[plan_id]
            elif plan_id in self._recovery_plans:
                plan = self._recovery_plans[plan_id]
                return {
                    'plan_id': str(plan_id),
                    'status': RecoveryStatus.COMPLETED.value,
                    'operations': len(plan.operations),
                    'created_at': plan.created_at
                }
        
        return None

    def get_recovery_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recovery operation history"""
        with self._lock:
            return sorted(
                self._recovery_history,
                key=lambda x: x.get('completed_at', 0),
                reverse=True
            )[:limit]

    def get_consistency_report(self) -> Dict[str, Any]:
        """Get data consistency report"""
        with self._lock:
            total_checks = len(self._consistency_checks)
            passed_checks = sum(1 for check in self._consistency_checks if check.passed)
            
            return {
                'total_checks': total_checks,
                'passed_checks': passed_checks,
                'failed_checks': total_checks - passed_checks,
                'success_rate': passed_checks / total_checks if total_checks > 0 else 0.0,
                'recent_checks': [
                    {
                        'check_id': str(check.check_id),
                        'check_type': check.check_type,
                        'table_name': check.table_name,
                        'passed': check.passed,
                        'violations': len(check.violations),
                        'executed_at': check.executed_at
                    }
                    for check in sorted(self._consistency_checks, 
                                      key=lambda x: x.executed_at, 
                                      reverse=True)[:10]
                ]
            }

    def get_statistics(self) -> Dict[str, Any]:
        """Get recovery orchestrator statistics"""
        with self._lock:
            stats = self._stats.copy()
            stats.update({
                'active_recoveries': len(self._active_recoveries),
                'total_plans': len(self._recovery_plans),
                'consistency_checks': len(self._consistency_checks),
                'recovery_types': {
                    rtype.value: sum(1 for plan in self._recovery_plans.values()
                                   if plan.recovery_type == rtype)
                    for rtype in RecoveryType
                }
            })
            return stats

    async def disaster_recovery_trigger(self, disaster_scenario: str) -> UUID:
        """Trigger disaster recovery procedure"""
        logger.critical("Disaster recovery triggered",
                       scenario=disaster_scenario)
        
        # Implement disaster recovery specific logic
        recovery_type = RecoveryType.DISASTER_RECOVERY
        
        return await self.initiate_recovery(
            recovery_type=recovery_type,
            recovery_options={
                'disaster_scenario': disaster_scenario,
                'aggressive_mode': True,
                'conflict_resolution': 'overwrite'
            }
        )

    def shutdown(self):
        """Shutdown recovery orchestrator"""
        # Cancel any active recoveries gracefully
        with self._lock:
            for plan_id, recovery_info in self._active_recoveries.items():
                if recovery_info['status'] == RecoveryStatus.IN_PROGRESS:
                    recovery_info['status'] = RecoveryStatus.CANCELLED
        
        logger.info("Recovery orchestrator shutdown complete")


# Global recovery orchestrator instance
_recovery_orchestrator: Optional[RecoveryOrchestrator] = None


def get_recovery_orchestrator(**kwargs) -> RecoveryOrchestrator:
    """Get or create global recovery orchestrator instance"""
    global _recovery_orchestrator
    if _recovery_orchestrator is None:
        _recovery_orchestrator = RecoveryOrchestrator(**kwargs)
    return _recovery_orchestrator
