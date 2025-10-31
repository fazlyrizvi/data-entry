"""
Error Recovery Module
Implements automated error recovery workflows, escalation procedures,
and resilience mechanisms for processing failures.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import threading
from queue import Queue
import hashlib
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecoveryAction(Enum):
    """Available recovery actions"""
    RETRY = "retry"
    SKIP = "skip"
    ESCALATE = "escalate"
    ROLLBACK = "rollback"
    COMPENSATE = "compensate"
    FALLBACK = "fallback"
    DEFER = "defer"
    QUARANTINE = "quarantine"

class RecoveryStatus(Enum):
    """Recovery workflow status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"

class EscalationLevel(Enum):
    """Escalation levels"""
    L1_SUPPORT = "l1_support"
    L2_SUPPORT = "l2_support"
    L3_SUPPORT = "l3_support"
    MANAGEMENT = "management"
    EXTERNAL_VENDOR = "external_vendor"

@dataclass
class ErrorContext:
    """Context information about an error"""
    error_id: str
    error_type: str
    error_message: str
    stack_trace: Optional[str]
    timestamp: datetime
    source_system: str
    user_id: Optional[str]
    request_id: Optional[str]
    document_id: Optional[str]
    severity: str
    metadata: Dict[str, Any]

@dataclass
class RecoveryStep:
    """Individual recovery step"""
    step_id: str
    action: RecoveryAction
    description: str
    parameters: Dict[str, Any]
    timeout_seconds: int = 300
    max_retries: int = 3
    retry_delay_seconds: int = 5
    dependencies: List[str] = None
    rollback_action: Optional[str] = None

@dataclass
class RecoveryWorkflow:
    """Complete recovery workflow"""
    workflow_id: str
    error_context: ErrorContext
    steps: List[RecoveryStep]
    status: RecoveryStatus
    current_step_index: int = 0
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempts: int = 0
    max_attempts: int = 3
    escalation_triggered: bool = False
    escalation_level: Optional[EscalationLevel] = None

@dataclass
class EscalationRule:
    """Escalation rule configuration"""
    rule_id: str
    name: str
    conditions: Dict[str, Any]
    escalation_level: EscalationLevel
    target_recipients: List[str]
    timeout_minutes: int
    max_escalations: int = 3
    is_active: bool = True

class RetryHandler:
    """Handles retry logic with exponential backoff"""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 300.0, backoff_multiplier: float = 2.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
    
    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """Determine if operation should be retried"""
        if attempt >= self.max_attempts:
            return False
        
        # Don't retry certain types of errors
        non_retryable_errors = [
            "AuthenticationError",
            "PermissionDeniedError",
            "ValidationError"
        ]
        
        return exception.__class__.__name__ not in non_retryable_errors
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay before next retry"""
        delay = self.base_delay * (self.backoff_multiplier ** attempt)
        return min(delay, self.max_delay)
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(attempt, e):
                    raise e
                
                if attempt < self.max_attempts:
                    delay = self.calculate_delay(attempt)
                    logger.info(f"Retrying operation (attempt {attempt}/{self.max_attempts}) after {delay}s delay")
                    await asyncio.sleep(delay)
        
        raise last_exception

class WorkflowEngine:
    """Engine for executing recovery workflows"""
    
    def __init__(self, notifier=None):
        self.active_workflows: Dict[str, RecoveryWorkflow] = {}
        self.completed_workflows: List[RecoveryWorkflow] = []
        self.workflow_queue = Queue()
        self.is_running = False
        self.threads = []
        self.notifier = notifier
        self.lock = threading.Lock()
        
        # Recovery action handlers
        self.action_handlers = {
            RecoveryAction.RETRY: self._handle_retry,
            RecoveryAction.SKIP: self._handle_skip,
            RecoveryAction.ESCALATE: self._handle_escalate,
            RecoveryAction.ROLLBACK: self._handle_rollback,
            RecoveryAction.COMPENSATE: self._handle_compensate,
            RecoveryAction.FALLBACK: self._handle_fallback,
            RecoveryAction.DEFER: self._handle_defer,
            RecoveryAction.QUARANTINE: self._handle_quarantine
        }
    
    def start(self):
        """Start workflow engine"""
        self.is_running = True
        
        # Start workflow processing thread
        workflow_thread = threading.Thread(target=self._process_workflows, daemon=True)
        workflow_thread.start()
        self.threads.append(workflow_thread)
        
        # Start workflow monitor thread
        monitor_thread = threading.Thread(target=self._monitor_workflows, daemon=True)
        monitor_thread.start()
        self.threads.append(monitor_thread)
        
        logger.info("Recovery workflow engine started")
    
    def stop(self):
        """Stop workflow engine"""
        self.is_running = False
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=5)
        
        logger.info("Recovery workflow engine stopped")
    
    def create_workflow(self, error_context: ErrorContext, recovery_plan: List[RecoveryStep]) -> str:
        """Create and queue recovery workflow"""
        workflow_id = f"workflow_{error_context.error_id}_{int(time.time())}"
        
        workflow = RecoveryWorkflow(
            workflow_id=workflow_id,
            error_context=error_context,
            steps=recovery_plan,
            status=RecoveryStatus.PENDING,
            created_at=datetime.now()
        )
        
        with self.lock:
            self.active_workflows[workflow_id] = workflow
        
        # Queue for processing
        self.workflow_queue.put(workflow)
        
        logger.info(f"Created recovery workflow: {workflow_id}")
        return workflow_id
    
    def _process_workflows(self):
        """Process workflows from queue"""
        while self.is_running:
            try:
                workflow = self.workflow_queue.get(timeout=1)
                self._execute_workflow(workflow)
                self.workflow_queue.task_done()
            except:
                continue
    
    def _monitor_workflows(self):
        """Monitor active workflows for timeouts and escalations"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                with self.lock:
                    for workflow in list(self.active_workflows.values()):
                        if workflow.status == RecoveryStatus.IN_PROGRESS:
                            self._check_workflow_timeout(workflow, current_time)
                
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Workflow monitoring error: {str(e)}")
    
    def _check_workflow_timeout(self, workflow: RecoveryWorkflow, current_time: datetime):
        """Check if workflow has timed out"""
        if workflow.started_at:
            timeout_threshold = workflow.started_at + timedelta(minutes=30)  # 30-minute timeout
            
            if current_time > timeout_threshold and not workflow.escalation_triggered:
                self._trigger_escalation(workflow, "Workflow timeout")
    
    def _execute_workflow(self, workflow: RecoveryWorkflow):
        """Execute recovery workflow"""
        logger.info(f"Executing workflow: {workflow.workflow_id}")
        
        workflow.status = RecoveryStatus.IN_PROGRESS
        workflow.started_at = datetime.now()
        workflow.attempts += 1
        
        try:
            for step_index in range(workflow.current_step_index, len(workflow.steps)):
                workflow.current_step_index = step_index
                step = workflow.steps[step_index]
                
                logger.info(f"Executing step {step_index + 1}/{len(workflow.steps)}: {step.description}")
                
                # Check dependencies
                if not self._check_dependencies(step, workflow):
                    logger.warning(f"Skipping step {step.step_id} due to unmet dependencies")
                    continue
                
                # Execute step
                success = self._execute_step(step, workflow)
                
                if not success:
                    logger.error(f"Step {step.step_id} failed")
                    workflow.status = RecoveryStatus.FAILED
                    self._trigger_escalation(workflow, f"Step {step.step_id} failed")
                    break
            
            if workflow.status == RecoveryStatus.IN_PROGRESS:
                workflow.status = RecoveryStatus.COMPLETED
                workflow.completed_at = datetime.now()
                logger.info(f"Workflow completed successfully: {workflow.workflow_id}")
            
        except Exception as e:
            logger.error(f"Workflow execution error: {str(e)}")
            workflow.status = RecoveryStatus.FAILED
            self._trigger_escalation(workflow, str(e))
        
        # Move to completed workflows
        with self.lock:
            if workflow.workflow_id in self.active_workflows:
                del self.active_workflows[workflow.workflow_id]
            self.completed_workflows.append(workflow)
    
    def _check_dependencies(self, step: RecoveryStep, workflow: RecoveryWorkflow) -> bool:
        """Check if step dependencies are met"""
        if not step.dependencies:
            return True
        
        for dep_step_id in step.dependencies:
            # Check if dependency step was completed
            dep_step_index = next(
                (i for i, s in enumerate(workflow.steps) if s.step_id == dep_step_id), 
                -1
            )
            
            if dep_step_index >= workflow.current_step_index:
                return False
        
        return True
    
    def _execute_step(self, step: RecoveryStep, workflow: RecoveryWorkflow) -> bool:
        """Execute individual recovery step"""
        handler = self.action_handlers.get(step.action)
        if not handler:
            logger.error(f"No handler for action: {step.action}")
            return False
        
        try:
            return handler(step, workflow)
        except Exception as e:
            logger.error(f"Step execution error: {str(e)}")
            return False
    
    def _handle_retry(self, step: RecoveryStep, workflow: RecoveryWorkflow) -> bool:
        """Handle retry action"""
        retry_handler = RetryHandler(
            max_attempts=step.max_retries,
            base_delay=step.retry_delay_seconds
        )
        
        async def retry_operation():
            # Simulate retry operation
            await asyncio.sleep(step.retry_delay_seconds)
            return True
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(retry_handler.execute_with_retry(retry_operation))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Retry failed: {str(e)}")
            return False
    
    def _handle_skip(self, step: RecoveryStep, workflow: RecoveryWorkflow) -> bool:
        """Handle skip action"""
        logger.info(f"Skipping step: {step.description}")
        return True
    
    def _handle_escalate(self, step: RecoveryStep, workflow: RecoveryWorkflow) -> bool:
        """Handle escalate action"""
        escalation_level = step.parameters.get('escalation_level', EscalationLevel.L1_SUPPORT)
        workflow.escalation_triggered = True
        workflow.escalation_level = escalation_level
        
        if self.notifier:
            escalation_data = {
                'workflow_id': workflow.workflow_id,
                'error_context': asdict(workflow.error_context),
                'escalation_level': escalation_level.value,
                'current_step': step.description
            }
            self.notifier.trigger_alert(escalation_data, source="recovery_engine")
        
        logger.warning(f"Escalation triggered: {escalation_level.value}")
        return True
    
    def _handle_rollback(self, step: RecoveryStep, workflow: RecoveryWorkflow) -> bool:
        """Handle rollback action"""
        # Simulate rollback operation
        logger.info(f"Executing rollback: {step.description}")
        
        # In a real implementation, this would:
        # 1. Identify what needs to be rolled back
        # 2. Execute rollback procedures
        # 3. Verify rollback success
        
        time.sleep(2)  # Simulate rollback time
        return True
    
    def _handle_compensate(self, step: RecoveryStep, workflow: RecoveryWorkflow) -> bool:
        """Handle compensate action"""
        logger.info(f"Executing compensation: {step.description}")
        
        # In a real implementation, this would:
        # 1. Apply compensation logic
        # 2. Update system state
        # 3. Log compensation actions
        
        time.sleep(1)  # Simulate compensation time
        return True
    
    def _handle_fallback(self, step: RecoveryStep, workflow: RecoveryWorkflow) -> bool:
        """Handle fallback action"""
        logger.info(f"Executing fallback: {step.description}")
        
        # In a real implementation, this would:
        # 1. Switch to alternative processing path
        # 2. Use fallback services/systems
        # 3. Continue with degraded functionality
        
        time.sleep(3)  # Simulate fallback activation time
        return True
    
    def _handle_defer(self, step: RecoveryStep, workflow: RecoveryWorkflow) -> bool:
        """Handle defer action"""
        defer_until = step.parameters.get('defer_until')
        if defer_until:
            # In a real implementation, this would:
            # 1. Schedule deferred action
            # 2. Set up monitoring for trigger conditions
            # 3. Update workflow status
            logger.info(f"Deferring action until: {defer_until}")
        
        return True
    
    def _handle_quarantine(self, step: RecoveryStep, workflow: RecoveryWorkflow) -> bool:
        """Handle quarantine action"""
        quarantine_reason = step.parameters.get('reason', 'Error quarantine')
        logger.info(f"Quarantining error: {quarantine_reason}")
        
        # In a real implementation, this would:
        # 1. Isolate the problematic data/process
        # 2. Create quarantine record
        # 3. Set up monitoring for quarantine items
        
        return True
    
    def _trigger_escalation(self, workflow: RecoveryWorkflow, reason: str):
        """Trigger escalation for workflow"""
        workflow.escalation_triggered = True
        workflow.status = RecoveryStatus.ESCALATED
        
        # Find escalation step or create one
        escalation_step = RecoveryStep(
            step_id="escalation",
            action=RecoveryAction.ESCALATE,
            description=f"Escalation: {reason}",
            parameters={'escalation_level': EscalationLevel.L2_SUPPORT}
        )
        
        self._execute_step(escalation_step, workflow)
        
        logger.warning(f"Escalation triggered for workflow {workflow.workflow_id}: {reason}")
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific workflow"""
        with self.lock:
            workflow = self.active_workflows.get(workflow_id)
            if workflow:
                return {
                    'workflow_id': workflow.workflow_id,
                    'status': workflow.status.value,
                    'current_step': workflow.current_step_index + 1,
                    'total_steps': len(workflow.steps),
                    'attempts': workflow.attempts,
                    'escalation_triggered': workflow.escalation_triggered,
                    'created_at': workflow.created_at.isoformat(),
                    'started_at': workflow.started_at.isoformat() if workflow.started_at else None,
                    'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None
                }
        return None
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow execution statistics"""
        with self.lock:
            active_count = len(self.active_workflows)
            completed_count = len(self.completed_workflows)
            
            # Calculate success rate
            successful_workflows = [
                w for w in self.completed_workflows 
                if w.status == RecoveryStatus.COMPLETED
            ]
            success_rate = len(successful_workflows) / max(1, completed_count)
            
            # Calculate average execution time
            completed_with_time = [
                w for w in self.completed_workflows 
                if w.started_at and w.completed_at
            ]
            avg_execution_time = 0
            if completed_with_time:
                total_time = sum([
                    (w.completed_at - w.started_at).total_seconds() 
                    for w in completed_with_time
                ])
                avg_execution_time = total_time / len(completed_with_time)
            
            # Count escalations
            escalated_count = len([
                w for w in self.completed_workflows 
                if w.escalation_triggered
            ])
            
            return {
                'active_workflows': active_count,
                'completed_workflows': completed_count,
                'success_rate': success_rate,
                'average_execution_time_seconds': avg_execution_time,
                'escalated_workflows': escalated_count,
                'escalation_rate': escalated_count / max(1, completed_count)
            }

class ResilienceManager:
    """Manages overall system resilience and recovery strategies"""
    
    def __init__(self, workflow_engine: WorkflowEngine, notifier=None):
        self.workflow_engine = workflow_engine
        self.notifier = notifier
        self.resilience_patterns = {}
        self.circuit_breakers = {}
        
        # Initialize default patterns
        self._initialize_resilience_patterns()
    
    def _initialize_resilience_patterns(self):
        """Initialize default resilience patterns"""
        
        # Circuit breaker pattern for external services
        self.resilience_patterns['circuit_breaker'] = {
            'failure_threshold': 5,
            'recovery_timeout': 60,
            'expected_exception': Exception
        }
        
        # Bulkhead pattern for resource isolation
        self.resilience_patterns['bulkhead'] = {
            'max_concurrent_requests': 100,
            'max_queue_size': 50
        }
        
        # Timeout pattern
        self.resilience_patterns['timeout'] = {
            'default_timeout': 30,
            'long_running_timeout': 300
        }
    
    def handle_error(self, error_context: ErrorContext) -> str:
        """Handle error and create appropriate recovery workflow"""
        
        # Determine recovery strategy based on error type
        recovery_plan = self._create_recovery_plan(error_context)
        
        # Create workflow
        workflow_id = self.workflow_engine.create_workflow(error_context, recovery_plan)
        
        return workflow_id
    
    def _create_recovery_plan(self, error_context: ErrorContext) -> List[RecoveryStep]:
        """Create recovery plan based on error context"""
        
        plan = []
        
        # Common first step: log and analyze
        plan.append(RecoveryStep(
            step_id="log_error",
            action=RecoveryAction.COMPENSATE,
            description="Log error details for analysis",
            parameters={'log_level': 'error'}
        ))
        
        # Error-type specific recovery steps
        if error_context.error_type == "processing_timeout":
            plan.extend([
                RecoveryStep(
                    step_id="retry_with_timeout",
                    action=RecoveryAction.RETRY,
                    description="Retry with extended timeout",
                    parameters={'timeout': 600, 'max_retries': 2}
                ),
                RecoveryStep(
                    step_id="fallback_processor",
                    action=RecoveryAction.FALLBACK,
                    description="Switch to alternative processor",
                    parameters={'fallback_service': 'backup_processor'}
                )
            ])
        
        elif error_context.error_type == "invalid_format":
            plan.extend([
                RecoveryStep(
                    step_id="validate_format",
                    action=RecoveryAction.COMPENSATE,
                    description="Validate and attempt format conversion",
                    parameters={'convert_formats': ['pdf', 'docx']}
                ),
                RecoveryStep(
                    step_id="quarantine_invalid",
                    action=RecoveryAction.QUARANTINE,
                    description="Quarantine invalid document",
                    parameters={'reason': 'Invalid format'}
                )
            ])
        
        elif error_context.error_type == "system_overload":
            plan.extend([
                RecoveryStep(
                    step_id="defer_processing",
                    action=RecoveryAction.DEFER,
                    description="Defer processing to reduce load",
                    parameters={'defer_minutes': 15}
                ),
                RecoveryStep(
                    step_id="scale_resources",
                    action=RecoveryAction.ESCALATE,
                    description="Escalate for resource scaling",
                    parameters={'escalation_level': EscalationLevel.L2_SUPPORT}
                )
            ])
        
        elif error_context.error_type == "network_error":
            plan.extend([
                RecoveryStep(
                    step_id="retry_with_backoff",
                    action=RecoveryAction.RETRY,
                    description="Retry with exponential backoff",
                    parameters={'max_retries': 3, 'base_delay': 5}
                ),
                RecoveryStep(
                    step_id="switch_endpoint",
                    action=RecoveryAction.FALLBACK,
                    description="Switch to backup endpoint",
                    parameters={'backup_endpoint': 'secondary_service'}
                )
            ])
        
        else:
            # Generic recovery plan
            plan.append(RecoveryStep(
                step_id="generic_retry",
                action=RecoveryAction.RETRY,
                description="Generic retry with standard settings",
                parameters={'max_retries': 2, 'timeout': 30}
            ))
        
        # Always end with escalation if all else fails
        plan.append(RecoveryStep(
            step_id="final_escalation",
            action=RecoveryAction.ESCALATE,
            description="Final escalation to support team",
            parameters={'escalation_level': EscalationLevel.L3_SUPPORT}
        ))
        
        return plan
    
    def get_resilience_metrics(self) -> Dict[str, Any]:
        """Get resilience and recovery metrics"""
        workflow_stats = self.workflow_engine.get_workflow_statistics()
        
        # Circuit breaker metrics
        circuit_breaker_stats = {}
        for service, cb in self.circuit_breakers.items():
            circuit_breaker_stats[service] = {
                'state': cb.get('state', 'closed'),
                'failure_count': cb.get('failure_count', 0),
                'last_failure_time': cb.get('last_failure_time')
            }
        
        return {
            'workflow_statistics': workflow_stats,
            'circuit_breakers': circuit_breaker_stats,
            'resilience_patterns': list(self.resilience_patterns.keys()),
            'total_recovery_workflows': workflow_stats.get('completed_workflows', 0),
            'system_health': 'healthy' if workflow_stats.get('success_rate', 0) > 0.8 else 'degraded'
        }
    
    def simulate_error_scenario(self, error_type: str, severity: str = "medium") -> str:
        """Simulate error scenario for testing recovery workflows"""
        
        error_context = ErrorContext(
            error_id=f"sim_{error_type}_{int(time.time())}",
            error_type=error_type,
            error_message=f"Simulated {error_type} error",
            stack_trace=None,
            timestamp=datetime.now(),
            source_system="simulation",
            severity=severity,
            metadata={'simulation': True, 'test_scenario': error_type}
        )
        
        return self.handle_error(error_context)