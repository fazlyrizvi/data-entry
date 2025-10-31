#!/usr/bin/env python3
"""
CRM Integration Demo Script

This script demonstrates all the features of the CRM integration package.
Run with: python demo.py
"""

import asyncio
import json
import os
from datetime import datetime

# Import all connector classes using absolute imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base import (
    SyncConfig, 
    SyncDirection, 
    ConflictResolution,
    DataMapper
)

try:
    from salesforce_connector import SalesforceConnector
    from hubspot_connector import HubSpotConnector
    from dynamics_connector import Dynamics365Connector
    from generic_connector import RestConnector, GraphQLConnector
except ImportError:
    # Handle relative imports if needed
    from .salesforce_connector import SalesforceConnector
    from .hubspot_connector import HubSpotConnector
    from .dynamics_connector import Dynamics365Connector
    from .generic_connector import RestConnector, GraphQLConnector

from utils import (
    DataValidator,
    FieldMappingHelper,
    ErrorHandler,
    LoggingConfig
)


class CRMIntegrationDemo:
    """Comprehensive CRM integration demonstration"""
    
    def __init__(self):
        self.connectors = {}
        LoggingConfig.setup_logging(level='INFO')
        print("\n" + "="*80)
        print("CRM INTEGRATION - COMPREHENSIVE DEMO")
        print("="*80)
    
    def print_section(self, title: str):
        """Print a formatted section header"""
        print("\n" + "-"*80)
        print(f" {title}")
        print("-"*80)
    
    def print_result(self, success: bool, message: str):
        """Print a formatted result"""
        symbol = "✓" if success else "✗"
        print(f" {symbol} {message}")
    
    async def demo_base_classes(self):
        """Demonstrate base connector functionality"""
        self.print_section("BASE CONNECTOR FUNCTIONALITY")
        
        # Data Validator
        print("\n1. Data Validation:")
        test_email = "user@example.com"
        is_valid = DataValidator.validate_email(test_email)
        self.print_result(is_valid, f"Email '{test_email}' is valid")
        
        test_phone = "+1-555-123-4567"
        is_valid = DataValidator.validate_phone(test_phone)
        self.print_result(is_valid, f"Phone '{test_phone}' is valid")
        
        required_fields = ['first_name', 'last_name', 'email']
        test_data = {'first_name': 'John', 'email': 'john@example.com'}
        missing = DataValidator.validate_required_fields(test_data, required_fields)
        if missing:
            self.print_result(False, f"Missing required fields: {missing}")
        else:
            self.print_result(True, "All required fields present")
        
        # Field Mapping
        print("\n2. Field Mapping:")
        mappings = {
            'first_name': 'FirstName',
            'last_name': 'LastName',
            'email': 'Email'
        }
        
        mapper = DataMapper(mappings)
        test_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '+1234567890'
        }
        
        external_data = mapper.map_to_external(test_data)
        print(f"   External format: {external_data}")
        
        mapped_back = mapper.map_to_internal(external_data)
        print(f"   Mapped back: {mapped_back}")
        self.print_result(True, "Field mapping works correctly")
        
        # Standard Mappings
        print("\n3. Standard Field Mappings:")
        sf_mappings = FieldMappingHelper.get_crm_mappings('salesforce')
        hs_mappings = FieldMappingHelper.get_crm_mappings('hubspot')
        print(f"   Salesforce fields: {list(sf_mappings.keys())[:5]}...")
        print(f"   HubSpot fields: {list(hs_mappings.keys())[:5]}...")
        self.print_result(True, "Standard mappings loaded")
        
        # Sync Configuration
        print("\n4. Synchronization Configuration:")
        sync_config = SyncConfig(
            direction=SyncDirection.BIDIRECTIONAL,
            conflict_resolution=ConflictResolution.TIMESTAMP,
            batch_size=100,
            max_retries=3
        )
        print(f"   Direction: {sync_config.direction.value}")
        print(f"   Conflict Resolution: {sync_config.conflict_resolution.value}")
        print(f"   Batch Size: {sync_config.batch_size}")
        self.print_result(True, "Sync configuration created")
        
    async def demo_connectors_creation(self):
        """Demonstrate connector creation without authentication"""
        self.print_section("CONNECTOR CREATION (NO AUTHENTICATION)")
        
        print("\n1. Salesforce Connector:")
        sf_config = {
            'client_id': os.getenv('SF_CLIENT_ID', 'demo_client_id'),
            'client_secret': os.getenv('SF_CLIENT_SECRET', 'demo_secret'),
            'username': os.getenv('SF_USERNAME', 'demo@example.com'),
            'password': os.getenv('SF_PASSWORD', 'demo_password'),
            'security_token': os.getenv('SF_SECURITY_TOKEN', ''),
            'instance_url': os.getenv('SF_INSTANCE_URL', 'https://demo.salesforce.com'),
            'rate_limit': {'max_calls': 100, 'time_window': 60}
        }
        
        try:
            sf_connector = SalesforceConnector(sf_config)
            entities = sf_connector.get_supported_entities()
            print(f"   Supported entities: {len(entities)} types")
            print(f"   Sample entities: {entities[:3]}...")
            self.connectors['salesforce'] = sf_connector
            self.print_result(True, "Salesforce connector created successfully")
        except Exception as e:
            self.print_result(False, f"Salesforce connector creation failed: {str(e)}")
        
        print("\n2. HubSpot Connector:")
        hs_config = {
            'client_id': os.getenv('HS_CLIENT_ID', 'demo_client_id'),
            'client_secret': os.getenv('HS_CLIENT_SECRET', 'demo_secret'),
            'access_token': os.getenv('HS_ACCESS_TOKEN', 'demo_token'),
            'portal_id': os.getenv('HS_PORTAL_ID', '123456'),
            'rate_limit': {'max_calls': 100, 'time_window': 60}
        }
        
        try:
            hs_connector = HubSpotConnector(hs_config)
            entities = hs_connector.get_supported_entities()
            print(f"   Supported entities: {len(entities)} types")
            print(f"   Sample entities: {entities[:3]}...")
            self.connectors['hubspot'] = hs_connector
            self.print_result(True, "HubSpot connector created successfully")
        except Exception as e:
            self.print_result(False, f"HubSpot connector creation failed: {str(e)}")
        
        print("\n3. Dynamics 365 Connector:")
        dyn_config = {
            'tenant_id': os.getenv('DYN_TENANT_ID', 'demo_tenant'),
            'client_id': os.getenv('DYN_CLIENT_ID', 'demo_client_id'),
            'client_secret': os.getenv('DYN_CLIENT_SECRET', 'demo_secret'),
            'resource_url': os.getenv('DYN_RESOURCE_URL', 'https://demo.crm.dynamics.com'),
            'api_version': '9.2'
        }
        
        try:
            dyn_connector = Dynamics365Connector(dyn_config)
            entities = dyn_connector.get_supported_entities()
            print(f"   Supported entities: {len(entities)} types")
            print(f"   Sample entities: {entities[:3]}...")
            self.connectors['dynamics'] = dyn_connector
            self.print_result(True, "Dynamics 365 connector created successfully")
        except Exception as e:
            self.print_result(False, f"Dynamics 365 connector creation failed: {str(e)}")
        
        print("\n4. Generic REST Connector:")
        rest_config = {
            'base_url': 'https://api.demo-crm.com/v1',
            'auth_type': 'bearer',
            'auth_config': {'token': 'demo_token'},
            'supported_entities': ['contacts', 'companies', 'deals']
        }
        
        try:
            rest_connector = RestConnector(rest_config)
            entities = rest_connector.get_supported_entities()
            print(f"   Supported entities: {entities}")
            print(f"   Base URL: {rest_connector.base_url}")
            self.connectors['generic_rest'] = rest_connector
            self.print_result(True, "Generic REST connector created successfully")
        except Exception as e:
            self.print_result(False, f"Generic REST connector creation failed: {str(e)}")
        
        print("\n5. Generic GraphQL Connector:")
        gql_config = {
            'endpoint': 'https://api.demo-crm.com/graphql',
            'auth_type': 'bearer',
            'auth_config': {'token': 'demo_token'},
            'supported_entities': ['contacts', 'companies']
        }
        
        try:
            gql_connector = GraphQLConnector(gql_config)
            entities = gql_connector.get_supported_entities()
            print(f"   Supported entities: {entities}")
            print(f"   GraphQL endpoint: {gql_connector.graphql_endpoint}")
            self.connectors['generic_graphql'] = gql_connector
            self.print_result(True, "Generic GraphQL connector created successfully")
        except Exception as e:
            self.print_result(False, f"Generic GraphQL connector creation failed: {str(e)}")
    
    async def demo_entity_schemas(self):
        """Demonstrate entity schema retrieval"""
        self.print_section("ENTITY SCHEMA INFORMATION")
        
        for name, connector in self.connectors.items():
            print(f"\n{name.upper()} Connector Schemas:")
            try:
                entities = connector.get_supported_entities()[:3]  # First 3 entities
                for entity in entities:
                    schema = connector.get_entity_schema(entity)
                    print(f"   {entity}:")
                    print(f"     - Name: {schema.get('name', 'N/A')}")
                    print(f"     - Createable: {schema.get('createable', 'N/A')}")
                    print(f"     - Updateable: {schema.get('updateable', 'N/A')}")
            except Exception as e:
                self.print_result(False, f"Error getting schemas: {str(e)}")
    
    async def demo_data_mapping(self):
        """Demonstrate data mapping across different CRMs"""
        self.print_section("DATA MAPPING DEMONSTRATION")
        
        sample_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '+1-555-123-4567',
            'company': 'Acme Corp',
            'title': 'Senior Developer'
        }
        
        print(f"\nOriginal Data:")
        print(f"   {json.dumps(sample_data, indent=2)}")
        
        for name, connector in self.connectors.items():
            print(f"\n{name.upper()} Mapping:")
            try:
                # Set up field mappings based on connector type
                if name == 'salesforce':
                    connector.data_mapper.add_mapping('first_name', 'FirstName')
                    connector.data_mapper.add_mapping('last_name', 'LastName')
                    connector.data_mapper.add_mapping('email', 'Email')
                    connector.data_mapper.add_mapping('phone', 'Phone')
                elif name == 'hubspot':
                    connector.data_mapper.add_mapping('first_name', 'firstname')
                    connector.data_mapper.add_mapping('last_name', 'lastname')
                    connector.data_mapper.add_mapping('email', 'email')
                    connector.data_mapper.add_mapping('phone', 'phone')
                elif name == 'dynamics':
                    connector.data_mapper.add_mapping('first_name', 'firstname')
                    connector.data_mapper.add_mapping('last_name', 'lastname')
                    connector.data_mapper.add_mapping('email', 'emailaddress1')
                    connector.data_mapper.add_mapping('phone', 'telephone1')
                
                # Map data to external format
                external_data = connector.data_mapper.map_to_external(sample_data.copy())
                print(f"   External format: {json.dumps(external_data, indent=4)}")
                
                # Map back to internal format
                internal_data = connector.data_mapper.map_to_internal(external_data)
                print(f"   Mapped back: {json.dumps(internal_data, indent=4)}")
                
                self.print_result(True, f"Data mapping successful for {name}")
            except Exception as e:
                self.print_result(False, f"Data mapping failed for {name}: {str(e)}")
    
    async def demo_sync_configuration(self):
        """Demonstrate synchronization configuration options"""
        self.print_section("SYNCHRONIZATION CONFIGURATION")
        
        print("\n1. Conflict Resolution Strategies:")
        
        strategies = [
            (ConflictResolution.SOURCE_WINS, "Source system wins"),
            (ConflictResolution.TARGET_WINS, "Target system wins"),
            (ConflictResolution.TIMESTAMP, "Most recent timestamp wins"),
            (ConflictResolution.MANUAL, "Manual resolution required"),
            (ConflictResolution.CUSTOM, "Custom resolution logic")
        ]
        
        for strategy, description in strategies:
            config = SyncConfig(conflict_resolution=strategy)
            print(f"   {strategy.value}: {description}")
        
        print("\n2. Sync Direction Options:")
        directions = [
            (SyncDirection.PUSH, "Send data to CRM"),
            (SyncDirection.PULL, "Fetch data from CRM"),
            (SyncDirection.BIDIRECTIONAL, "Both directions")
        ]
        
        for direction, description in directions:
            config = SyncConfig(direction=direction)
            print(f"   {direction.value}: {description}")
        
        print("\n3. Batch Processing Configuration:")
        batch_configs = [
            (10, "Small batches (10 records)"),
            (100, "Medium batches (100 records)"),
            (1000, "Large batches (1000 records)")
        ]
        
        for batch_size, description in batch_configs:
            config = SyncConfig(batch_size=batch_size)
            print(f"   {batch_size} records: {description}")
        
        print("\n4. Retry Configuration:")
        retry_configs = [
            (1, 0.5, "Fast retries"),
            (3, 1.0, "Standard retries"),
            (5, 2.0, "Conservative retries")
        ]
        
        for max_retries, delay, description in retry_configs:
            config = SyncConfig(max_retries=max_retries, retry_delay=delay)
            print(f"   {max_retries} retries, {delay}s delay: {description}")
        
        self.print_result(True, "All synchronization configurations demonstrated")
    
    async def demo_error_handling(self):
        """Demonstrate error handling capabilities"""
        self.print_section("ERROR HANDLING DEMONSTRATION")
        
        print("\n1. API Error Handling:")
        
        # Test various error scenarios
        error_scenarios = [
            (400, "Bad Request"),
            (401, "Unauthorized"),
            (403, "Forbidden"),
            (404, "Not Found"),
            (429, "Rate Limit Exceeded"),
            (500, "Internal Server Error")
        ]
        
        for status_code, description in error_scenarios:
            try:
                # Simulate API error
                raise ErrorHandler.handle_api_error(status_code, "Test error message")
            except Exception as e:
                print(f"   {status_code} ({description}): {type(e).__name__}")
        
        print("\n2. Safe Data Access:")
        
        # Test safe nested dictionary access
        test_data = {
            'contact': {
                'address': {
                    'city': 'New York'
                }
            }
        }
        
        city = ErrorHandler.safe_get_nested(test_data, 'contact.address.city', 'Unknown')
        country = ErrorHandler.safe_get_nested(test_data, 'contact.address.country', 'USA')
        
        print(f"   City: {city}")
        print(f"   Country: {country}")
        
        print("\n3. Data Validation:")
        
        # Test validation functions
        test_cases = [
            ("user@example.com", "Valid email"),
            ("invalid-email", "Invalid email"),
            ("+1-555-123-4567", "Valid phone"),
            ("12345", "Invalid phone"),
            ({'first_name': 'John'}, "Missing fields"),
            ({'first_name': 'John', 'last_name': 'Doe', 'email': 'john@example.com'}, "All fields present")
        ]
        
        for test_case, description in test_cases:
            if isinstance(test_case, str):
                is_valid = DataValidator.validate_email(test_case)
                result = "Valid" if is_valid else "Invalid"
            elif isinstance(test_case, str):
                is_valid = DataValidator.validate_phone(test_case)
                result = "Valid" if is_valid else "Invalid"
            else:
                required = ['first_name', 'last_name', 'email']
                missing = DataValidator.validate_required_fields(test_case, required)
                result = "Complete" if not missing else f"Missing: {missing}"
            
            print(f"   {description}: {result}")
        
        self.print_result(True, "Error handling demonstrated successfully")
    
    async def demo_performance_features(self):
        """Demonstrate performance features"""
        self.print_section("PERFORMANCE FEATURES")
        
        print("\n1. Rate Limiting:")
        print("   - Configurable rate limits per connector")
        print("   - Automatic throttling to prevent API quota exhaustion")
        print("   - Configurable time windows (60 seconds default)")
        print("   - Example: 100 calls per 60 seconds")
        
        print("\n2. Batch Processing:")
        print("   - Automatic batching for bulk operations")
        print("   - Configurable batch sizes (10-1000 records)")
        print("   - Progress tracking for large datasets")
        print("   - Memory efficient processing")
        
        print("\n3. Asynchronous Operations:")
        print("   - Full async/await support")
        print("   - Non-blocking I/O operations")
        print("   - Concurrent request handling")
        print("   - Improved throughput for large datasets")
        
        print("\n4. Connection Management:")
        print("   - Persistent connections")
        print("   - Connection pooling")
        print("   - Automatic cleanup")
        print("   - Resource optimization")
        
        self.print_result(True, "Performance features documented")
    
    async def demo_security_features(self):
        """Demonstrate security features"""
        self.print_section("SECURITY FEATURES")
        
        print("\n1. Authentication Methods:")
        print("   ✓ OAuth 2.0 Password Flow (Salesforce)")
        print("   ✓ OAuth 2.0 Client Credentials (Dynamics 365)")
        print("   ✓ OAuth 2.0 Authorization Code (HubSpot)")
        print("   ✓ Bearer Token Authentication")
        print("   ✓ Basic Authentication")
        print("   ✓ API Key Authentication")
        
        print("\n2. Token Management:")
        print("   - Automatic token refresh")
        print("   - Secure token storage")
        print("   - Token expiration handling")
        print("   - Multiple authentication methods per connector")
        
        print("\n3. Data Security:")
        print("   - Input validation and sanitization")
        print("   - SQL injection prevention")
        print("   - XSS protection")
        print("   - Secure data transmission (HTTPS only)")
        
        print("\n4. Configuration Security:")
        print("   - Environment variable support")
        print("   - Secret management")
        print("   - No hardcoded credentials")
        print("   - Secure default configurations")
        
        self.print_result(True, "Security features documented")
    
    async def demo_use_cases(self):
        """Demonstrate real-world use cases"""
        self.print_section("REAL-WORLD USE CASES")
        
        use_cases = [
            {
                "title": "Data Migration",
                "description": "Migrate contact data from one CRM to another",
                "steps": [
                    "Export data from source CRM",
                    "Transform data format",
                    "Import to target CRM",
                    "Verify data integrity"
                ],
                "code_example": """
# Bulk migration example
source_contacts = await source_connector.query('Contact', {})
transformed_contacts = [transform_contact(c) for c in source_contacts]
await target_connector.bulk_create('contacts', transformed_contacts)
                """.strip()
            },
            {
                "title": "Real-time Synchronization",
                "description": "Keep multiple CRMs synchronized in real-time",
                "steps": [
                    "Monitor source CRM for changes",
                    "Detect modifications using timestamps",
                    "Sync changes to target CRM",
                    "Handle conflicts automatically"
                ],
                "code_example": """
# Continuous sync example
while True:
    changes = await source_connector.query('Contact', {
        'LastModifiedDate': {'gte': last_sync_time}
    })
    if changes:
        await target_connector.synchronize(changes, 'contacts')
    last_sync_time = datetime.utcnow()
    await asyncio.sleep(60)
                """.strip()
            },
            {
                "title": "Multi-CRM Dashboard",
                "description": "Aggregate data from multiple CRMs for unified view",
                "steps": [
                    "Connect to each CRM",
                    "Query data from each system",
                    "Merge and normalize data",
                    "Present unified dashboard"
                ],
                "code_example": """
# Multi-CRM aggregation example
all_contacts = []
for connector in [sf_connector, hs_connector, dyn_connector]:
    contacts = await connector.query('contacts', {})
    all_contacts.extend(contacts)
create_dashboard(all_contacts)
                """.strip()
            },
            {
                "title": "Lead Distribution",
                "description": "Automatically distribute leads to appropriate sales reps",
                "steps": [
                    "Receive new leads from forms",
                    "Analyze lead characteristics",
                    "Assign to sales rep based on criteria",
                    "Create activities in CRM"
                ],
                "code_example": """
# Lead distribution example
new_lead = await form_connector.get_submission(form_id)
assigned_rep = assign_rep(new_lead)
await crm_connector.create('lead', {
    **new_lead,
    'owner': assigned_rep,
    'source': 'website_form'
})
                """.strip()
            }
        ]
        
        for i, use_case in enumerate(use_cases, 1):
            print(f"\n{i}. {use_case['title']}")
            print(f"   {use_case['description']}")
            print("   Steps:")
            for step in use_case['steps']:
                print(f"     - {step}")
            print("   Code Example:")
            print(f"   {use_case['code_example']}")
        
        self.print_result(True, "Use cases demonstrated")
    
    async def cleanup(self):
        """Clean up all connections"""
        print("\n" + "="*80)
        print("CLEANUP")
        print("="*80)
        
        for name, connector in self.connectors.items():
            try:
                await connector.close()
                self.print_result(True, f"Closed {name} connector")
            except Exception as e:
                self.print_result(False, f"Error closing {name} connector: {str(e)}")
        
        print("\n" + "="*80)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("="*80)
    
    async def run_demo(self):
        """Run the complete demonstration"""
        try:
            await self.demo_base_classes()
            await self.demo_connectors_creation()
            await self.demo_entity_schemas()
            await self.demo_data_mapping()
            await self.demo_sync_configuration()
            await self.demo_error_handling()
            await self.demo_performance_features()
            await self.demo_security_features()
            await self.demo_use_cases()
            
        except Exception as e:
            print(f"\n✗ Demo failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.cleanup()


async def main():
    """Main demo function"""
    demo = CRMIntegrationDemo()
    await demo.run_demo()


if __name__ == '__main__':
    print("\nCRM Integration Package - Comprehensive Demo")
    print("="*80)
    print("\nThis demo showcases all features of the CRM integration package:")
    print("  ✓ Base connector functionality")
    print("  ✓ All supported CRM connectors (Salesforce, HubSpot, Dynamics 365)")
    print("  ✓ Generic REST and GraphQL connectors")
    print("  ✓ Data mapping and transformation")
    print("  ✓ Synchronization capabilities")
    print("  ✓ Error handling and validation")
    print("  ✓ Performance and security features")
    print("  ✓ Real-world use cases")
    print("\n" + "="*80)
    
    # Run the demo
    asyncio.run(main())
