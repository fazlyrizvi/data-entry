#!/usr/bin/env python3
"""
Startup Script

Convenience script for starting webhook handlers with different configurations.
"""

import os
import sys
import argparse
import signal
import threading
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import webhook_handler
from monitoring_dashboard import MonitoringDashboard
from config import ConfigManager, get_development_config, get_production_config, get_testing_config


class WebhookManager:
    """Manage webhook services"""
    
    def __init__(self):
        self.webhook_app = None
        self.dashboard_app = None
        self.running = False
    
    def setup_webhook_service(self, config_type: str = "development") -> None:
        """
        Setup webhook service based on configuration
        
        Args:
            config_type: Configuration type (development, production, testing)
        """
        # Load configuration
        if config_type == "development":
            config = get_development_config()
        elif config_type == "production":
            config = get_production_config()
        elif config_type == "testing":
            config = get_testing_config()
        else:
            config = get_development_config()
        
        # Setup webhook handler
        self.webhook_app = webhook_handler
        
        # Configure based on environment
        if config_type == "production":
            # Add production endpoints
            if not any(ep.enabled for ep in self.webhook_app.endpoints.values()):
                print("Adding production endpoints...")
                # In production, load endpoints from database or config
                pass
        
        print(f"Webhook service configured for {config_type}")
    
    def setup_monitoring(self, webhook_url: str = "http://localhost:5000") -> None:
        """
        Setup monitoring dashboard
        
        Args:
            webhook_url: URL of webhook service
        """
        self.dashboard_app = MonitoringDashboard(webhook_url)
        print(f"Monitoring dashboard configured for {webhook_url}")
    
    def start_services(self, host: str = "0.0.0.0", port: int = 5000, 
                      enable_monitoring: bool = True, debug: bool = False) -> None:
        """
        Start webhook services
        
        Args:
            host: Host to bind to
            port: Port for webhook service
            enable_monitoring: Whether to enable monitoring dashboard
            debug: Enable debug mode
        """
        try:
            self.running = True
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            print(f"🚀 Starting Webhook Handler on {host}:{port}")
            
            # Start services in threads
            threads = []
            
            # Start webhook service
            webhook_thread = threading.Thread(
                target=self._run_webhook_service,
                args=(host, port, debug),
                daemon=True
            )
            webhook_thread.start()
            threads.append(webhook_thread)
            
            # Start monitoring dashboard if enabled
            if enable_monitoring:
                dashboard_thread = threading.Thread(
                    target=self._run_monitoring_dashboard,
                    daemon=True
                )
                dashboard_thread.start()
                threads.append(dashboard_thread)
                print("📊 Monitoring dashboard will be available at http://localhost:5001")
            
            print("✅ Services started successfully!")
            print("\n📝 Available endpoints:")
            print(f"   Webhook Service: http://{host}:{port}")
            print(f"   Health Check:    http://{host}:{port}/health")
            print(f"   Metrics:         http://{host}:{port}/metrics")
            if enable_monitoring:
                print(f"   Dashboard:       http://localhost:5001")
            print("\n💡 Press Ctrl+C to stop all services")
            
            # Keep main thread alive
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            
        except Exception as e:
            print(f"❌ Error starting services: {e}")
            sys.exit(1)
        finally:
            self._shutdown()
    
    def _run_webhook_service(self, host: str, port: int, debug: bool) -> None:
        """Run webhook service"""
        try:
            self.webhook_app.start(host=host, port=port, debug=debug)
        except Exception as e:
            print(f"❌ Webhook service error: {e}")
            self.running = False
    
    def _run_monitoring_dashboard(self) -> None:
        """Run monitoring dashboard"""
        try:
            self.dashboard_app.start()
        except Exception as e:
            print(f"❌ Monitoring dashboard error: {e}")
    
    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals"""
        print("\n🛑 Shutdown signal received, stopping services...")
        self.running = False
    
    def _shutdown(self) -> None:
        """Shutdown all services"""
        print("🔄 Shutting down services...")
        
        if self.webhook_app and hasattr(self.webhook_app, 'router'):
            try:
                self.webhook_app.router.shutdown(timeout=10)
                print("✅ Event router shutdown complete")
            except Exception as e:
                print(f"⚠️  Error shutting down router: {e}")
        
        if self.dashboard_app:
            try:
                self.dashboard_app.metrics_collector.stop()
                print("✅ Metrics collector stopped")
            except Exception as e:
                print(f"⚠️  Error stopping metrics collector: {e}")
        
        print("👋 Services stopped. Goodbye!")
    
    def run_tests(self) -> None:
        """Run webhook tests"""
        try:
            from test_webhooks import run_comprehensive_test
            print("🧪 Running comprehensive webhook tests...")
            results = run_comprehensive_test()
            
            # Print summary
            all_passed = (
                results['health'].get('status') == 'healthy' and
                all(results.get(key, {}).get('success', False) 
                    for key in ['custom_webhook', 'stripe_webhook', 'github_webhook']) and
                results['signature_verification']['verification_working']
            )
            
            if all_passed:
                print("✅ All tests passed!")
            else:
                print("❌ Some tests failed")
                return 1
                
        except ImportError:
            print("❌ Test module not found")
            return 1
        except Exception as e:
            print(f"❌ Test execution error: {e}")
            return 1
        
        return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Webhook Handler Manager")
    parser.add_argument(
        '--mode', 
        choices=['dev', 'prod', 'test'], 
        default='dev',
        help='Operation mode (dev=development, prod=production, test=testing)'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port for webhook service (default: 5000)'
    )
    parser.add_argument(
        '--no-monitoring',
        action='store_true',
        help='Disable monitoring dashboard'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run tests instead of starting server'
    )
    
    args = parser.parse_args()
    
    # Create manager
    manager = WebhookManager()
    
    if args.test:
        # Run tests
        return manager.run_tests()
    
    # Setup services
    config_mode = {
        'dev': 'development',
        'prod': 'production',
        'test': 'testing'
    }[args.mode]
    
    manager.setup_webhook_service(config_mode)
    
    if not args.no_monitoring:
        webhook_url = f"http://{args.host}:{args.port}"
        manager.setup_monitoring(webhook_url)
    
    # Start services
    manager.start_services(
        host=args.host,
        port=args.port,
        enable_monitoring=not args.no_monitoring,
        debug=args.debug
    )
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
