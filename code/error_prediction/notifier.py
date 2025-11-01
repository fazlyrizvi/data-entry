"""
Notification Module
Handles email and Slack notifications with error categorization,
escalation procedures, and smart alerting logic.
"""

import smtplib
import ssl
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import threading
from queue import Queue
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    """Available notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"
    IN_APP = "in_app"

class AlertLevel(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    RESOLVED = "resolved"

@dataclass
class NotificationRule:
    """Rule for triggering notifications"""
    rule_id: str
    name: str
    conditions: Dict[str, Any]
    channels: List[NotificationChannel]
    recipients: List[str]
    cooldown_minutes: int = 60
    max_alerts_per_hour: int = 10
    escalation_after_minutes: int = 30
    is_active: bool = True

@dataclass
class Alert:
    """Alert object for notifications"""
    alert_id: str
    title: str
    message: str
    level: AlertLevel
    source: str
    timestamp: datetime
    metadata: Dict[str, Any]
    channels: List[NotificationChannel]
    recipients: List[str]
    status: str = "pending"  # pending, sent, failed, escalated
    retry_count: int = 0
    max_retries: int = 3

class EmailNotifier:
    """Email notification handler"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, 
                 from_email: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.context = ssl.create_default_context()
    
    def send_email(self, to_emails: List[str], subject: str, body: str, 
                   html_body: Optional[str] = None, attachments: Optional[List[str]] = None) -> bool:
        """Send email notification"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            
            # Add body
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    self._attach_file(msg, file_path)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=self.context)
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_emails}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Attach file to email"""
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {file_path.split("/")[-1]}'
            )
            msg.attach(part)
        except Exception as e:
            logger.error(f"Failed to attach file {file_path}: {str(e)}")

class SlackNotifier:
    """Slack notification handler"""
    
    def __init__(self, webhook_url: str, bot_token: Optional[str] = None, channel: str = "#alerts"):
        self.webhook_url = webhook_url
        self.bot_token = bot_token
        self.channel = channel
        self.session = requests.Session()
    
    def send_slack_message(self, message: str, color: str = "#ff0000", 
                          title: Optional[str] = None, fields: Optional[List[Dict]] = None,
                          blocks: Optional[List[Dict]] = None) -> bool:
        """Send Slack message"""
        try:
            if blocks:
                # Use Blocks API for rich formatting
                payload = {
                    "channel": self.channel,
                    "blocks": blocks
                }
            else:
                # Use simple webhook format
                payload = {
                    "channel": self.channel,
                    "text": message,
                    "attachments": [{
                        "color": color,
                        "title": title or "Alert",
                        "text": message,
                        "fields": fields or []
                    }]
                }
            
            response = self.session.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("Slack message sent successfully")
                return True
            else:
                logger.error(f"Slack API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Slack message: {str(e)}")
            return False
    
    def create_rich_alert(self, alert: Alert) -> List[Dict]:
        """Create rich Slack alert with blocks"""
        # Color mapping based on alert level
        color_map = {
            AlertLevel.CRITICAL: "#ff0000",
            AlertLevel.WARNING: "#ffa500",
            AlertLevel.INFO: "#00ff00",
            AlertLevel.RESOLVED: "#808080"
        }
        
        color = color_map.get(alert.level, "#ff0000")
        
        # Create blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{alert.level.value.upper()}: {alert.title}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": alert.message
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Source:* {alert.source}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:* {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
        
        # Add metadata fields if available
        if alert.metadata:
            metadata_fields = []
            for key, value in list(alert.metadata.items())[:5]:  # Limit to 5 fields
                metadata_fields.append({
                    "type": "mrkdwn",
                    "text": f"*{key}:* {value}"
                })
            
            if metadata_fields:
                blocks.append({
                    "type": "section",
                    "fields": metadata_fields
                })
        
        # Add action buttons for critical alerts
        if alert.level == AlertLevel.CRITICAL:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Acknowledge"
                        },
                        "style": "primary",
                        "action_id": "acknowledge_alert",
                        "value": alert.alert_id
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Details"
                        },
                        "action_id": "view_details",
                        "value": alert.alert_id
                    }
                ]
            })
        
        return blocks

class NotificationRuleEngine:
    """Engine for managing notification rules and triggers"""
    
    def __init__(self):
        self.rules: Dict[str, NotificationRule] = {}
        self.alert_history: List[Alert] = []
        self.cooldown_tracker: Dict[str, datetime] = {}
        self.rate_limiter: Dict[str, List[datetime]] = {}
        
    def add_rule(self, rule: NotificationRule):
        """Add notification rule"""
        self.rules[rule.rule_id] = rule
        logger.info(f"Added notification rule: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """Remove notification rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed notification rule: {rule_id}")
    
    def check_and_trigger_alert(self, event_data: Dict[str, Any], source: str = "system") -> List[Alert]:
        """Check rules and trigger appropriate alerts"""
        triggered_alerts = []
        
        for rule in self.rules.values():
            if not rule.is_active:
                continue
            
            # Check cooldown
            if self._is_in_cooldown(rule.rule_id, rule.cooldown_minutes):
                continue
            
            # Check rate limiting
            if self._is_rate_limited(rule.rule_id, rule.max_alerts_per_hour):
                continue
            
            # Evaluate conditions
            if self._evaluate_conditions(rule.conditions, event_data):
                # Create alert
                alert = self._create_alert(rule, event_data, source)
                triggered_alerts.append(alert)
                
                # Update tracking
                self._update_tracking(rule.rule_id)
        
        return triggered_alerts
    
    def _is_in_cooldown(self, rule_id: str, cooldown_minutes: int) -> bool:
        """Check if rule is in cooldown period"""
        last_trigger = self.cooldown_tracker.get(rule_id)
        if last_trigger:
            cooldown_delta = timedelta(minutes=cooldown_minutes)
            return datetime.now() - last_trigger < cooldown_delta
        return False
    
    def _is_rate_limited(self, rule_id: str, max_alerts_per_hour: int) -> bool:
        """Check if rule exceeds rate limit"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        if rule_id not in self.rate_limiter:
            self.rate_limiter[rule_id] = []
        
        # Clean old timestamps
        self.rate_limiter[rule_id] = [
            timestamp for timestamp in self.rate_limiter[rule_id]
            if timestamp > hour_ago
        ]
        
        return len(self.rate_limiter[rule_id]) >= max_alerts_per_hour
    
    def _evaluate_conditions(self, conditions: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """Evaluate if event matches rule conditions"""
        for key, expected_value in conditions.items():
            if key not in event_data:
                return False
            
            actual_value = event_data[key]
            
            # Handle different comparison operators
            if isinstance(expected_value, dict):
                operator = expected_value.get('operator', '==')
                value = expected_value['value']
                
                if operator == '>' and not (actual_value > value):
                    return False
                elif operator == '<' and not (actual_value < value):
                    return False
                elif operator == '>=' and not (actual_value >= value):
                    return False
                elif operator == '<=' and not (actual_value <= value):
                    return False
                elif operator == '!=' and not (actual_value != value):
                    return False
                elif operator == 'in' and actual_value not in value:
                    return False
                elif operator == 'not_in' and actual_value in value:
                    return False
                elif operator == 'contains' and value not in str(actual_value):
                    return False
                elif not (actual_value == value):
                    return False
            else:
                # Simple equality check
                if actual_value != expected_value:
                    return False
        
        return True
    
    def _create_alert(self, rule: NotificationRule, event_data: Dict[str, Any], source: str) -> Alert:
        """Create alert from rule and event data"""
        # Determine alert level
        level = AlertLevel.WARNING
        if 'severity' in event_data:
            severity_map = {
                'critical': AlertLevel.CRITICAL,
                'high': AlertLevel.WARNING,
                'medium': AlertLevel.WARNING,
                'low': AlertLevel.INFO
            }
            level = severity_map.get(event_data['severity'], AlertLevel.WARNING)
        
        # Generate alert ID
        alert_id = f"alert_{rule.rule_id}_{int(datetime.now().timestamp())}"
        
        # Create message
        title = event_data.get('title', f"Alert from rule: {rule.name}")
        message = event_data.get('message', f"Event triggered rule: {rule.name}")
        
        alert = Alert(
            alert_id=alert_id,
            title=title,
            message=message,
            level=level,
            source=source,
            timestamp=datetime.now(),
            metadata=event_data.copy(),
            channels=rule.channels,
            recipients=rule.recipients
        )
        
        self.alert_history.append(alert)
        return alert
    
    def _update_tracking(self, rule_id: str):
        """Update cooldown and rate limiting trackers"""
        now = datetime.now()
        self.cooldown_tracker[rule_id] = now
        
        if rule_id not in self.rate_limiter:
            self.rate_limiter[rule_id] = []
        self.rate_limiter[rule_id].append(now)

class NotificationOrchestrator:
    """Main notification orchestrator"""
    
    def __init__(self, email_config: Dict[str, str], slack_config: Dict[str, str]):
        # Initialize notifiers
        self.email_notifier = EmailNotifier(
            smtp_server=email_config['smtp_server'],
            smtp_port=int(email_config['smtp_port']),
            username=email_config['username'],
            password=email_config['password'],
            from_email=email_config['from_email']
        )
        
        self.slack_notifier = SlackNotifier(
            webhook_url=slack_config['webhook_url'],
            bot_token=slack_config.get('bot_token'),
            channel=slack_config.get('channel', '#alerts')
        )
        
        # Initialize rule engine
        self.rule_engine = NotificationRuleEngine()
        
        # Initialize queues and threads
        self.alert_queue = Queue()
        self.notification_queue = Queue()
        self.is_running = False
        self.threads = []
        
        # Load default rules
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default notification rules"""
        
        # Critical error rule
        critical_rule = NotificationRule(
            rule_id="critical_error",
            name="Critical Error Alert",
            conditions={
                "error_probability": {"operator": ">", "value": 0.8},
                "severity": {"in": ["critical", "high"]}
            },
            channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
            recipients=["admin@company.com"],
            cooldown_minutes=15,
            max_alerts_per_hour=20,
            escalation_after_minutes=5
        )
        self.rule_engine.add_rule(critical_rule)
        
        # High error rate rule
        high_rate_rule = NotificationRule(
            rule_id="high_error_rate",
            name="High Error Rate Alert",
            conditions={
                "error_rate": {"operator": ">", "value": 0.15},
                "window_minutes": {"operator": ">=", "value": 60}
            },
            channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
            recipients=["ops@company.com"],
            cooldown_minutes=30,
            max_alerts_per_hour=10
        )
        self.rule_engine.add_rule(high_rate_rule)
        
        # System overload rule
        overload_rule = NotificationRule(
            rule_id="system_overload",
            name="System Overload Alert",
            conditions={
                "error_type": "system_overload",
                "processing_time": {"operator": ">", "value": 300}
            },
            channels=[NotificationChannel.SLACK],
            recipients=["#devops"],
            cooldown_minutes=45,
            max_alerts_per_hour=15
        )
        self.rule_engine.add_rule(overload_rule)
        
        # Prediction accuracy drop rule
        accuracy_rule = NotificationRule(
            rule_id="accuracy_drop",
            name="Prediction Accuracy Drop",
            conditions={
                "accuracy": {"operator": "<", "value": 0.7},
                "samples": {"operator": ">=", "value": 50}
            },
            channels=[NotificationChannel.EMAIL],
            recipients=["ml-team@company.com"],
            cooldown_minutes=120,
            max_alerts_per_hour=5
        )
        self.rule_engine.add_rule(accuracy_rule)
        
        logger.info("Default notification rules loaded")
    
    def start(self):
        """Start notification orchestrator"""
        self.is_running = True
        
        # Start alert processing thread
        alert_thread = threading.Thread(target=self._process_alerts, daemon=True)
        alert_thread.start()
        self.threads.append(alert_thread)
        
        # Start notification sending thread
        notification_thread = threading.Thread(target=self._send_notifications, daemon=True)
        notification_thread.start()
        self.threads.append(notification_thread)
        
        logger.info("Notification orchestrator started")
    
    def stop(self):
        """Stop notification orchestrator"""
        self.is_running = False
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=5)
        
        logger.info("Notification orchestrator stopped")
    
    def trigger_alert(self, event_data: Dict[str, Any], source: str = "system") -> List[str]:
        """Trigger alert based on event data"""
        alerts = self.rule_engine.check_and_trigger_alert(event_data, source)
        alert_ids = []
        
        for alert in alerts:
            self.alert_queue.put(alert)
            alert_ids.append(alert.alert_id)
        
        return alert_ids
    
    def _process_alerts(self):
        """Process alerts in queue"""
        while self.is_running:
            try:
                alert = self.alert_queue.get(timeout=1)
                self._process_single_alert(alert)
                self.alert_queue.task_done()
            except:
                continue
    
    def _process_single_alert(self, alert: Alert):
        """Process single alert"""
        logger.info(f"Processing alert: {alert.alert_id}")
        
        # Add to notification queue
        self.notification_queue.put(alert)
    
    def _send_notifications(self):
        """Send notifications from queue"""
        while self.is_running:
            try:
                alert = self.notification_queue.get(timeout=1)
                self._send_alert(alert)
                self.notification_queue.task_done()
            except:
                continue
    
    def _send_alert(self, alert: Alert):
        """Send alert through configured channels"""
        success_count = 0
        
        for channel in alert.channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    if self._send_email_alert(alert):
                        success_count += 1
                
                elif channel == NotificationChannel.SLACK:
                    if self._send_slack_alert(alert):
                        success_count += 1
                
                elif channel == NotificationChannel.WEBHOOK:
                    if self._send_webhook_alert(alert):
                        success_count += 1
                        
            except Exception as e:
                logger.error(f"Failed to send alert via {channel.value}: {str(e)}")
        
        # Update alert status
        if success_count > 0:
            alert.status = "sent"
        else:
            alert.status = "failed"
            if alert.retry_count < alert.max_retries:
                alert.retry_count += 1
                # Re-queue for retry
                self.notification_queue.put(alert)
    
    def _send_email_alert(self, alert: Alert) -> bool:
        """Send email alert"""
        subject = f"[{alert.level.value.upper()}] {alert.title}"
        
        # Create email body
        body = f"""
        Alert Details:
        
        Title: {alert.title}
        Level: {alert.level.value.upper()}
        Source: {alert.source}
        Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        
        Message:
        {alert.message}
        
        Metadata:
        {json.dumps(alert.metadata, indent=2, default=str)}
        """
        
        # Create HTML body
        html_body = f"""
        <html>
        <body>
        <h2 style="color: {'red' if alert.level == AlertLevel.CRITICAL else 'orange'};">
            [{alert.level.value.upper()}] {alert.title}
        </h2>
        <p><strong>Source:</strong> {alert.source}</p>
        <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Message:</strong> {alert.message}</p>
        
        <h3>Metadata:</h3>
        <pre>{json.dumps(alert.metadata, indent=2, default=str)}</pre>
        </body>
        </html>
        """
        
        return self.email_notifier.send_email(
            to_emails=alert.recipients,
            subject=subject,
            body=body,
            html_body=html_body
        )
    
    def _send_slack_alert(self, alert: Alert) -> bool:
        """Send Slack alert"""
        blocks = self.slack_notifier.create_rich_alert(alert)
        
        return self.slack_notifier.send_slack_message(
            message=alert.message,
            title=alert.title,
            blocks=blocks
        )
    
    def _send_webhook_alert(self, alert: Alert) -> bool:
        """Send webhook alert"""
        try:
            webhook_payload = {
                "alert_id": alert.alert_id,
                "title": alert.title,
                "message": alert.message,
                "level": alert.level.value,
                "source": alert.source,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata
            }
            
            response = requests.post(
                "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
                json=webhook_payload,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Webhook alert failed: {str(e)}")
            return False
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get notification statistics"""
        recent_alerts = [
            alert for alert in self.rule_engine.alert_history
            if alert.timestamp > datetime.now() - timedelta(hours=24)
        ]
        
        total_alerts = len(recent_alerts)
        sent_alerts = len([a for a in recent_alerts if a.status == "sent"])
        failed_alerts = len([a for a in recent_alerts if a.status == "failed"])
        
        # Count by level
        level_counts = {}
        for alert in recent_alerts:
            level = alert.level.value
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # Count by channel
        channel_counts = {}
        for alert in recent_alerts:
            for channel in alert.channels:
                channel_name = channel.value
                channel_counts[channel_name] = channel_counts.get(channel_name, 0) + 1
        
        return {
            "total_alerts_24h": total_alerts,
            "sent_alerts": sent_alerts,
            "failed_alerts": failed_alerts,
            "success_rate": sent_alerts / max(1, total_alerts),
            "alerts_by_level": level_counts,
            "alerts_by_channel": channel_counts,
            "most_active_rule": max(self.rule_engine.rate_limiter.keys(), 
                                  key=lambda k: len(self.rule_engine.rate_limiter[k])) 
                                  if self.rule_engine.rate_limiter else "None"
        }
    
    def create_escalation_policy(self, policy_data: Dict[str, Any]):
        """Create escalation policy for alerts"""
        # This would integrate with external escalation systems
        # For now, we'll simulate escalation logic
        pass
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get notification system health status"""
        return {
            "status": "healthy" if self.is_running else "stopped",
            "active_rules": len([r for r in self.rule_engine.rules.values() if r.is_active]),
            "pending_alerts": self.alert_queue.qsize(),
            "pending_notifications": self.notification_queue.qsize(),
            "total_alerts_sent": len([a for a in self.rule_engine.alert_history if a.status == "sent"]),
            "thread_count": len(self.threads)
        }