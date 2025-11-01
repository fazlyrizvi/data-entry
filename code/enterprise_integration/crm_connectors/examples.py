"""
CRM Integration Example

Demonstrates usage of all CRM connectors with example scenarios.
"""

import asyncio
import json
from typing import Dict, Any, List

from .salesforce_connector import SalesforceConnector
from .hubspot_connector import HubSpotConnector
from .dynamics_connector import Dynamics365Connector
from .generic_connector import GenericConnector, RestConnector, GraphQLConnector
from .base import SyncConfig, SyncDirection, ConflictResolution
from .utils import LoggingConfig


class CRMIntegrationDemo:
    """Demonstration of CRM integration capabilities"""
    
    def __init__(self):
        self.connectors = {}
        LoggingConfig.setup_logging(level='INFO')
    
    async def setup_salesforce(self, config: Dict[str, Any]):
        """Setup Salesforce connector"""
        self.connectors['salesforce'] = SalesforceConnector(config)
        await self.connectors['salesforce'].authenticate()
        print("✓ Salesforce connector initialized")
    
    async def setup_hubspot(self, config: Dict[str, Any]):
        """Setup HubSpot connector"""
        self.connectors['hubspot'] = HubSpotConnector(config)
        await self.connectors['hubspot'].authenticate()
        print("✓ HubSpot connector initialized")
    
    async def setup_dynamics(self, config: Dict[str, Any]):
        """Setup Dynamics 365 connector"""
        self.connectors['dynamics'] = Dynamics365Connector(config)
        await self.connectors['dynamics'].authenticate()
        print("✓ Dynamics 365 connector initialized")
    
    async def setup_generic_rest(self, config: Dict[str, Any]):
        """Setup generic REST connector"""
        self.connectors['generic_rest'] = RestConnector(config)
        await self.connectors['generic_rest'].authenticate()
        print("✓ Generic REST connector initialized")
    
    async def setup_generic_graphql(self, config: Dict[str, Any]):
        """Setup generic GraphQL connector"""
        self.connectors['generic_graphql'] = GraphQLConnector(config)
        await self.connectors['generic_graphql'].authenticate()
        print("✓ Generic GraphQL connector initialized")
    
    async def demonstrate_basic_operations(self, connector_name: str, entity_type: str = 'contacts'):
        """Demonstrate basic CRUD operations"""
        if connector_name not in self.connectors:
            print(f"Connector {connector_name} not found")
            return
        
        connector = self.connectors[connector_name]
        print(f"\n=== Basic Operations on {connector_name} ===")
        
        try:
            # Create a sample record
            print(f"Creating {entity_type} record...")
            sample_data = {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
                'phone': '+1234567890'
            }
            
            # Add connector-specific field mapping
            if connector_name == 'salesforce':
                sample_data = connector.data_mapper.map_to_external(sample_data)
            elif connector_name == 'hubspot':
                sample_data['email'] = sample_data['email']
            
            created = await connector.create(entity_type, sample_data)
            record_id = created.get('id')
            print(f"✓ Created record with ID: {record_id}")
            
            if record_id:
                # Read the record
                print(f"Reading {entity_type} record...")
                record = await connector.read(entity_type, record_id)
                print(f"✓ Retrieved record: {record.get('first_name', 'N/A')} {record.get('last_name', 'N/A')}")
                
                # Update the record
                print(f"Updating {entity_type} record...")
                update_data = {'last_name': 'Smith'}
                updated = await connector.update(entity_type, record_id, update_data)
                print(f"✓ Updated record successfully")
                
                # Query records
                print(f"Querying {entity_type} records...")
                filters = {'email': {'like': 'john'}}
                records = await connector.query(entity_type, filters, limit=10)
                print(f"✓ Found {len(records)} matching records")
                
                # Clean up
                print(f"Deleting {entity_type} record...")
                await connector.delete(entity_type, record_id)
                print(f"✓ Deleted record successfully")
            
        except Exception as e:
            print(f"✗ Error during basic operations: {str(e)}")
    
    async def demonstrate_bulk_operations(self, connector_name: str, entity_type: str = 'contacts'):
        """Demonstrate bulk operations"""
        if connector_name not in self.connectors:
            print(f"Connector {connector_name} not found")
            return
        
        connector = self.connectors[connector_name]
        print(f"\n=== Bulk Operations on {connector_name} ===")
        
        try:
            # Create multiple sample records
            print("Creating bulk records...")
            sample_records = []
            for i in range(5):
                record = {
                    'first_name': f'Contact{i+1}',
                    'last_name': 'Test',
                    'email': f'contact{i+1}@example.com',
                    'phone': f'+123456789{i}'
                }
                sample_records.append(record)
            
            # Bulk create
            created_records = await connector.bulk_create(entity_type, sample_records, batch_size=2)
            print(f"✓ Created {len(created_records)} records")
            
            # Bulk update
            if created_records and isinstance(created_records[0], dict):
                print("Updating bulk records...")
                update_records = []
                for i, record in enumerate(created_records):
                    if 'id' in record:
                        update_record = {'id': record['id'], 'last_name': f'Updated{i+1}'}
                        update_records.append(update_record)
                
                if update_records:
                    updated_records = await connector.bulk_update(entity_type, update_records, batch_size=2)
                    print(f"✓ Updated {len(updated_records)} records")
                    
                    # Clean up
                    print("Deleting bulk records...")
                    record_ids = [r.get('id') for r in updated_records if 'id' in r]
                    if record_ids:
                        deleted_records = await connector.bulk_delete(entity_type, record_ids, batch_size=2)
                        print(f"✓ Deleted {len(deleted_records)} records")
            
        except Exception as e:
            print(f"✗ Error during bulk operations: {str(e)}")
    
    async def demonstrate_synchronization(self, source_crm: str, target_crm: str, 
                                        entity_type: str = 'contacts'):
        """Demonstrate data synchronization between CRMs"""
        if source_crm not in self.connectors or target_crm not in self.connectors:
            print(f"Required connectors not found")
            return
        
        print(f"\n=== Synchronization: {source_crm} → {target_crm} ===")
        
        try:
            source_connector = self.connectors[source_crm]
            target_connector = self.connectors[target_crm]
            
            # Get sample data from source
            print(f"Fetching data from {source_crm}...")
            try:
                source_data = await source_connector.query(entity_type, {}, limit=10)
                print(f"✓ Retrieved {len(source_data)} records from {source_crm}")
                
                if not source_data:
                    # Create sample data if none exists
                    print("Creating sample data for demonstration...")
                    sample_record = {
                        'first_name': 'Sync',
                        'last_name': 'Test',
                        'email': 'sync.test@example.com'
                    }
                    await source_connector.create(entity_type, sample_record)
                    source_data = await source_connector.query(entity_type, {}, limit=10)
                    print(f"✓ Created and retrieved {len(source_data)} records")
                
                # Configure synchronization
                sync_config = SyncConfig(
                    direction=SyncDirection.PUSH,
                    conflict_resolution=ConflictResolution.TIMESTAMP,
                    batch_size=5
                )
                
                # Perform synchronization
                print(f"Synchronizing {len(source_data)} records to {target_crm}...")
                result = await target_connector.synchronize(
                    source_data, entity_type, sync_config
                )
                
                print(f"✓ Synchronization completed:")
                print(f"  - Records processed: {result.records_processed}")
                print(f"  - Records succeeded: {result.records_succeeded}")
                print(f"  - Records failed: {result.records_failed}")
                print(f"  - Conflicts: {len(result.conflicts)}")
                print(f"  - Errors: {len(result.errors)}")
                print(f"  - Execution time: {result.execution_time:.2f}s")
                
            except Exception as e:
                print(f"✗ Error during synchronization: {str(e)}")
        
        except Exception as e:
            print(f"✗ Error during synchronization demo: {str(e)}")
    
    async def demonstrate_data_mapping(self, connector_name: str, entity_type: str = 'contacts'):
        """Demonstrate data mapping capabilities"""
        if connector_name not in self.connectors:
            print(f"Connector {connector_name} not found")
            return
        
        connector = self.connectors[connector_name]
        print(f"\n=== Data Mapping on {connector_name} ===")
        
        try:
            # Add some field mappings
            if connector_name == 'salesforce':
                connector.data_mapper.add_mapping('first_name', 'FirstName')
                connector.data_mapper.add_mapping('last_name', 'LastName')
                connector.data_mapper.add_mapping('email', 'Email')
            elif connector_name == 'hubspot':
                connector.data_mapper.add_mapping('first_name', 'firstname')
                connector.data_mapper.add_mapping('last_name', 'lastname')
                connector.data_mapper.add_mapping('email', 'email')
            elif connector_name == 'dynamics':
                connector.data_mapper.add_mapping('first_name', 'firstname')
                connector.data_mapper.add_mapping('last_name', 'lastname')
                connector.data_mapper.add_mapping('email', 'emailaddress1')
            
            # Test data mapping
            sample_data = {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
                'phone': '+1234567890'
            }
            
            print("Original data:", sample_data)
            
            # Map to external format
            external_data = connector.data_mapper.map_to_external(sample_data)
            print("External format:", external_data)
            
            # Map back to internal format
            internal_data = connector.data_mapper.map_to_internal(external_data)
            print("Internal format:", internal_data)
            
            print("✓ Data mapping demonstration completed")
            
        except Exception as e:
            print(f"✗ Error during data mapping demo: {str(e)}")
    
    async def test_connection(self, connector_name: str):
        """Test connection to CRM"""
        if connector_name not in self.connectors:
            print(f"Connector {connector_name} not found")
            return
        
        connector = self.connectors[connector_name]
        print(f"\n=== Testing {connector_name} Connection ===")
        
        try:
            result = await connector.test_connection()
            
            if result['success']:
                print(f"✓ Connection to {connector_name} successful")
                print(f"  Timestamp: {result['timestamp']}")
            else:
                print(f"✗ Connection to {connector_name} failed")
                print(f"  Error: {result['message']}")
                print(f"  Timestamp: {result['timestamp']}")
            
        except Exception as e:
            print(f"✗ Error testing {connector_name} connection: {str(e)}")
    
    async def get_supported_entities(self, connector_name: str):
        """Get supported entities from CRM"""
        if connector_name not in self.connectors:
            print(f"Connector {connector_name} not found")
            return
        
        connector = self.connectors[connector_name]
        print(f"\n=== {connector_name} Supported Entities ===")
        
        try:
            entities = connector.get_supported_entities()
            print(f"Supported entities ({len(entities)}):")
            for entity in entities[:10]:  # Show first 10
                print(f"  - {entity}")
            if len(entities) > 10:
                print(f"  ... and {len(entities) - 10} more")
            
            # Get schema for first entity
            if entities:
                first_entity = entities[0]
                schema = connector.get_entity_schema(first_entity)
                print(f"\nSchema for {first_entity}:")
                print(f"  Name: {schema.get('name', 'N/A')}")
                print(f"  Description: {schema.get('description', 'N/A')}")
                print(f"  Createable: {schema.get('createable', 'N/A')}")
                print(f"  Updateable: {schema.get('updateable', 'N/A')}")
            
        except Exception as e:
            print(f"✗ Error getting {connector_name} entities: {str(e)}")
    
    async def cleanup(self):
        """Cleanup all connections"""
        print("\n=== Cleanup ===")
        for name, connector in self.connectors.items():
            try:
                await connector.close()
                print(f"✓ Closed {name} connector")
            except Exception as e:
                print(f"✗ Error closing {name} connector: {str(e)}")


# Example usage scenarios
async def salesforce_example():
    """Example: Working with Salesforce"""
    print("\n" + "="*60)
    print("SALESFORCE EXAMPLE")
    print("="*60)
    
    config = {
        'client_id': 'your_salesforce_client_id',
        'client_secret': 'your_salesforce_client_secret',
        'username': 'your_salesforce_username',
        'password': 'your_salesforce_password',
        'security_token': 'your_salesforce_security_token',
        'instance_url': 'https://your-instance.salesforce.com',
        'api_version': 'v58.0',
        'rate_limit': {'max_calls': 100, 'time_window': 60},
        'retry': {'max_retries': 3, 'base_delay': 1.0}
    }
    
    demo = CRMIntegrationDemo()
    
    try:
        await demo.setup_salesforce(config)
        await demo.test_connection('salesforce')
        await demo.get_supported_entities('salesforce')
        await demo.demonstrate_data_mapping('salesforce', 'contacts')
        await demo.demonstrate_basic_operations('salesforce', 'contacts')
        await demo.demonstrate_bulk_operations('salesforce', 'contacts')
    finally:
        await demo.cleanup()


async def hubspot_example():
    """Example: Working with HubSpot"""
    print("\n" + "="*60)
    print("HUBSPOT EXAMPLE")
    print("="*60)
    
    config = {
        'client_id': 'your_hubspot_client_id',
        'client_secret': 'your_hubspot_client_secret',
        'access_token': 'your_hubspot_access_token',
        'refresh_token': 'your_hubspot_refresh_token',
        'portal_id': 'your_hubspot_portal_id',
        'rate_limit': {'max_calls': 100, 'time_window': 60},
        'retry': {'max_retries': 3, 'base_delay': 1.0}
    }
    
    demo = CRMIntegrationDemo()
    
    try:
        await demo.setup_hubspot(config)
        await demo.test_connection('hubspot')
        await demo.get_supported_entities('hubspot')
        await demo.demonstrate_data_mapping('hubspot', 'contacts')
        await demo.demonstrate_basic_operations('hubspot', 'contacts')
        await demo.demonstrate_bulk_operations('hubspot', 'contacts')
        
        # Demonstrate form submission (HubSpot specific)
        if 'hubspot' in demo.connectors:
            connector = demo.connectors['hubspot']
            print("\n=== HubSpot Form Submission ===")
            form_data = {
                'email': 'test@example.com',
                'firstname': 'Test',
                'lastname': 'User'
            }
            try:
                # Note: You need a valid form_id and portal_id
                print("Form submission would require valid form_id")
                print("Example form data:", form_data)
            except Exception as e:
                print(f"Form submission error: {str(e)}")
    finally:
        await demo.cleanup()


async def dynamics_example():
    """Example: Working with Dynamics 365"""
    print("\n" + "="*60)
    print("MICROSOFT DYNAMICS 365 EXAMPLE")
    print("="*60)
    
    config = {
        'tenant_id': 'your_azure_tenant_id',
        'client_id': 'your_azure_app_client_id',
        'client_secret': 'your_azure_app_client_secret',
        'resource_url': 'https://yourorg.crm.dynamics.com',
        'api_version': '9.2',
        'rate_limit': {'max_calls': 100, 'time_window': 60},
        'retry': {'max_retries': 3, 'base_delay': 1.0}
    }
    
    demo = CRMIntegrationDemo()
    
    try:
        await demo.setup_dynamics(config)
        await demo.test_connection('dynamics')
        await demo.get_supported_entities('dynamics')
        await demo.demonstrate_data_mapping('dynamics', 'contacts')
        await demo.demonstrate_basic_operations('dynamics', 'contacts')
        await demo.demonstrate_bulk_operations('dynamics', 'contacts')
        
        # Demonstrate Dynamics-specific features
        if 'dynamics' in demo.connectors:
            connector = demo.connectors['dynamics']
            print("\n=== Dynamics 365 Specific Features ===")
            try:
                whoami = await connector.who_am_i()
                print("WhoAmI result:", whoami)
            except Exception as e:
                print(f"WhoAmI error: {str(e)}")
    finally:
        await demo.cleanup()


async def generic_rest_example():
    """Example: Working with generic REST API"""
    print("\n" + "="*60)
    print("GENERIC REST API EXAMPLE")
    print("="*60)
    
    config = {
        'base_url': 'https://api.example-crm.com/v1',
        'auth_type': 'bearer',
        'auth_config': {
            'token': 'your_api_token'
        },
        'headers': {
            'User-Agent': 'CRM-Integration/1.0'
        },
        'timeout': 30,
        'rate_limit': {'max_calls': 100, 'time_window': 60},
        'retry': {'max_retries': 3, 'base_delay': 1.0},
        'supported_entities': ['contacts', 'companies', 'deals']
    }
    
    demo = CRMIntegrationDemo()
    
    try:
        await demo.setup_generic_rest(config)
        await demo.test_connection('generic_rest')
        await demo.get_supported_entities('generic_rest')
        await demo.demonstrate_basic_operations('generic_rest', 'contacts')
    finally:
        await demo.cleanup()


async def generic_graphql_example():
    """Example: Working with generic GraphQL API"""
    print("\n" + "="*60)
    print("GENERIC GRAPHQL API EXAMPLE")
    print("="*60)
    
    config = {
        'endpoint': 'https://api.example-crm.com/graphql',
        'auth_type': 'bearer',
        'auth_config': {
            'token': 'your_graphql_token'
        },
        'supported_entities': ['contacts', 'companies', 'deals']
    }
    
    demo = CRMIntegrationDemo()
    
    try:
        await demo.setup_generic_graphql(config)
        await demo.test_connection('generic_graphql')
        await demo.get_supported_entities('generic_graphql')
        await demo.demonstrate_basic_operations('generic_graphql', 'contacts')
    finally:
        await demo.cleanup()


async def cross_crm_synchronization_example():
    """Example: Synchronization between different CRMs"""
    print("\n" + "="*60)
    print("CROSS-CRM SYNCHRONIZATION EXAMPLE")
    print("="*60)
    
    # Note: This requires valid credentials for multiple CRMs
    salesforce_config = {
        'client_id': 'your_salesforce_client_id',
        'client_secret': 'your_salesforce_client_secret',
        'username': 'your_salesforce_username',
        'password': 'your_salesforce_password',
        'security_token': 'your_salesforce_security_token',
        'instance_url': 'https://your-instance.salesforce.com',
        'api_version': 'v58.0'
    }
    
    hubspot_config = {
        'client_id': 'your_hubspot_client_id',
        'client_secret': 'your_hubspot_client_secret',
        'access_token': 'your_hubspot_access_token',
        'portal_id': 'your_hubspot_portal_id'
    }
    
    demo = CRMIntegrationDemo()
    
    try:
        # Setup both connectors
        await demo.setup_salesforce(salesforce_config)
        await demo.setup_hubspot(hubspot_config)
        
        # Test connections
        await demo.test_connection('salesforce')
        await demo.test_connection('hubspot')
        
        # Demonstrate synchronization
        await demo.demonstrate_synchronization('salesforce', 'hubspot', 'contacts')
        
    finally:
        await demo.cleanup()


async def main():
    """Run all examples"""
    print("CRM Integration Examples")
    print("="*60)
    print("Note: These examples require valid API credentials.")
    print("Update the configuration dictionaries with your actual credentials.")
    print("="*60)
    
    examples = [
        ('Salesforce Example', salesforce_example),
        ('HubSpot Example', hubspot_example),
        ('Dynamics 365 Example', dynamics_example),
        ('Generic REST Example', generic_rest_example),
        ('Generic GraphQL Example', generic_graphql_example),
        ('Cross-CRM Synchronization', cross_crm_synchronization_example)
    ]
    
    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\n✗ {name} failed: {str(e)}")
            print("Make sure to update the configuration with valid credentials.")
    
    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60)


if __name__ == '__main__':
    asyncio.run(main())
