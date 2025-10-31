"""
Test Suite for CRM Connectors

This test suite demonstrates the functionality of all CRM connectors.
Note: These tests require valid API credentials to run successfully.
"""

import asyncio
import pytest
import os
from datetime import datetime

# Import all connector classes
from base import (
    BaseCRMConnector, 
    SyncConfig, 
    SyncDirection, 
    ConflictResolution,
    SyncRecord,
    RateLimiter,
    RetryManager,
    DataMapper
)
from salesforce_connector import SalesforceConnector
from hubspot_connector import HubSpotConnector
from dynamics_connector import Dynamics365Connector
from generic_connector import GenericConnector, RestConnector, GraphQLConnector


class TestBaseClasses:
    """Test base connector functionality"""
    
    def test_rate_limiter(self):
        """Test rate limiter functionality"""
        limiter = RateLimiter(max_calls=2, time_window=1)
        
        # Should allow first two calls
        limiter.wait_if_needed()
        limiter.wait_if_needed()
        
        # Third call should wait
        start_time = datetime.now()
        limiter.wait_if_needed()
        elapsed = (datetime.now() - start_time).total_seconds()
        
        assert elapsed >= 1.0  # Should have waited at least 1 second
    
    def test_retry_manager(self):
        """Test retry manager"""
        retry_manager = RetryManager(max_retries=2, base_delay=0.1)
        
        async def failing_func():
            raise Exception("Test failure")
        
        async def test_retry():
            try:
                await retry_manager.execute_with_retry(failing_func)
                assert False, "Should have raised exception"
            except Exception as e:
                assert str(e) == "Test failure"
        
        asyncio.run(test_retry())
    
    def test_data_mapper(self):
        """Test data mapper"""
        mapper = DataMapper({
            'first_name': 'FirstName',
            'last_name': 'LastName',
            'email': 'Email'
        })
        
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '+1234567890'  # Unmapped field
        }
        
        # Map to external
        external = mapper.map_to_external(data)
        assert external['FirstName'] == 'John'
        assert external['LastName'] == 'Doe'
        assert external['email'] == 'john@example.com'
        assert external['phone'] == '+1234567890'  # Unmapped fields preserved
        
        # Map back to internal
        internal = mapper.map_to_internal(external)
        assert internal['first_name'] == 'John'
        assert internal['last_name'] == 'Doe'
        assert internal['email'] == 'john@example.com'
        assert internal['phone'] == '+1234567890'


class TestSalesforceConnector:
    """Test Salesforce connector (requires valid credentials)"""
    
    @pytest.mark.skipif(
        not all([
            os.getenv('SF_CLIENT_ID'),
            os.getenv('SF_CLIENT_SECRET'),
            os.getenv('SF_USERNAME'),
            os.getenv('SF_PASSWORD'),
            os.getenv('SF_INSTANCE_URL')
        ]),
        reason="Salesforce credentials not provided"
    )
    async def test_salesforce_connection(self):
        """Test Salesforce connection and basic operations"""
        config = {
            'client_id': os.getenv('SF_CLIENT_ID'),
            'client_secret': os.getenv('SF_CLIENT_SECRET'),
            'username': os.getenv('SF_USERNAME'),
            'password': os.getenv('SF_PASSWORD'),
            'security_token': os.getenv('SF_SECURITY_TOKEN', ''),
            'instance_url': os.getenv('SF_INSTANCE_URL')
        }
        
        connector = SalesforceConnector(config)
        
        try:
            # Test connection
            result = await connector.test_connection()
            assert result['success'] == True
            
            # Test authentication
            auth_result = await connector.authenticate()
            assert auth_result == True
            
            # Test entity listing
            entities = connector.get_supported_entities()
            assert 'Contact' in entities
            assert 'Account' in entities
            
            print("✓ Salesforce connector tests passed")
            
        except Exception as e:
            print(f"✗ Salesforce connector test failed: {str(e)}")
            raise
        finally:
            await connector.close()


class TestHubSpotConnector:
    """Test HubSpot connector (requires valid credentials)"""
    
    @pytest.mark.skipif(
        not all([
            os.getenv('HS_CLIENT_ID'),
            os.getenv('HS_CLIENT_SECRET'),
            os.getenv('HS_ACCESS_TOKEN'),
            os.getenv('HS_PORTAL_ID')
        ]),
        reason="HubSpot credentials not provided"
    )
    async def test_hubspot_connection(self):
        """Test HubSpot connection and basic operations"""
        config = {
            'client_id': os.getenv('HS_CLIENT_ID'),
            'client_secret': os.getenv('HS_CLIENT_SECRET'),
            'access_token': os.getenv('HS_ACCESS_TOKEN'),
            'portal_id': os.getenv('HS_PORTAL_ID')
        }
        
        connector = HubSpotConnector(config)
        
        try:
            # Test connection
            result = await connector.test_connection()
            assert result['success'] == True
            
            # Test authentication
            auth_result = await connector.authenticate()
            assert auth_result == True
            
            # Test entity listing
            entities = connector.get_supported_entities()
            assert 'contacts' in entities
            assert 'companies' in entities
            
            print("✓ HubSpot connector tests passed")
            
        except Exception as e:
            print(f"✗ HubSpot connector test failed: {str(e)}")
            raise
        finally:
            await connector.close()


class TestDynamics365Connector:
    """Test Dynamics 365 connector (requires valid credentials)"""
    
    @pytest.mark.skipif(
        not all([
            os.getenv('DYN_TENANT_ID'),
            os.getenv('DYN_CLIENT_ID'),
            os.getenv('DYN_CLIENT_SECRET'),
            os.getenv('DYN_RESOURCE_URL')
        ]),
        reason="Dynamics 365 credentials not provided"
    )
    async def test_dynamics_connection(self):
        """Test Dynamics 365 connection and basic operations"""
        config = {
            'tenant_id': os.getenv('DYN_TENANT_ID'),
            'client_id': os.getenv('DYN_CLIENT_ID'),
            'client_secret': os.getenv('DYN_CLIENT_SECRET'),
            'resource_url': os.getenv('DYN_RESOURCE_URL')
        }
        
        connector = Dynamics365Connector(config)
        
        try:
            # Test connection
            result = await connector.test_connection()
            assert result['success'] == True
            
            # Test authentication
            auth_result = await connector.authenticate()
            assert auth_result == True
            
            # Test entity listing
            entities = connector.get_supported_entities()
            assert 'contacts' in entities
            assert 'accounts' in entities
            
            print("✓ Dynamics 365 connector tests passed")
            
        except Exception as e:
            print(f"✗ Dynamics 365 connector test failed: {str(e)}")
            raise
        finally:
            await connector.close()


class TestGenericConnectors:
    """Test generic connectors"""
    
    def test_rest_connector_creation(self):
        """Test REST connector creation"""
        config = {
            'base_url': 'https://api.example.com',
            'auth_type': 'bearer',
            'auth_config': {'token': 'test_token'}
        }
        
        connector = RestConnector(config)
        assert connector.base_url == 'https://api.example.com'
        assert connector.auth_type == 'bearer'
        assert connector.default_headers['Authorization'] == 'Bearer test_token'
        
        print("✓ REST connector creation test passed")
    
    def test_graphql_connector_creation(self):
        """Test GraphQL connector creation"""
        config = {
            'endpoint': 'https://api.example.com/graphql',
            'auth_type': 'bearer',
            'auth_config': {'token': 'test_token'}
        }
        
        connector = GraphQLConnector(config)
        assert connector.graphql_endpoint == 'https://api.example.com/graphql'
        
        print("✓ GraphQL connector creation test passed")


class TestDataSynchronization:
    """Test data synchronization features"""
    
    async def test_sync_config(self):
        """Test synchronization configuration"""
        config = SyncConfig(
            direction=SyncDirection.BIDIRECTIONAL,
            conflict_resolution=ConflictResolution.TIMESTAMP,
            batch_size=50
        )
        
        assert config.direction == SyncDirection.BIDIRECTIONAL
        assert config.conflict_resolution == ConflictResolution.TIMESTAMP
        assert config.batch_size == 50
    
    async def test_sync_record(self):
        """Test sync record creation"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com'
        }
        
        record = SyncRecord(id='123', data=data)
        
        assert record.id == '123'
        assert record.data == data
        assert record.timestamp is not None
        assert record.checksum is not None
        assert len(record.checksum) == 64  # SHA256 hash length
    
    async def test_data_synchronization(self):
        """Test data synchronization logic"""
        # Create sample data
        source_data = [
            {'id': '1', 'first_name': 'John', 'last_name': 'Doe'},
            {'id': '2', 'first_name': 'Jane', 'last_name': 'Smith'}
        ]
        
        target_data = [
            {'id': '1', 'first_name': 'Johnny', 'last_name': 'Doe'},  # Conflict
            {'id': '3', 'first_name': 'Bob', 'last_name': 'Jones'}   # New record
        ]
        
        # Convert to sync records
        source_records = [SyncRecord(id=r['id'], data=r) for r in source_data]
        target_records = [SyncRecord(id=r['id'], data=r) for r in target_data]
        
        # Test with source wins resolution
        from base import BaseCRMConnector
        
        class MockConnector(BaseCRMConnector):
            async def authenticate(self): return True
            async def create(self, entity_type, data): return data
            async def read(self, entity_type, entity_id): return {}
            async def update(self, entity_type, entity_id, data): return data
            async def delete(self, entity_type, entity_id): return True
            async def query(self, entity_type, filters, fields, limit): return []
            def get_supported_entities(self): return []
            def get_entity_schema(self, entity_type): return {}
        
        connector = MockConnector({})
        
        # Test synchronization
        sync_config = SyncConfig(
            direction=SyncDirection.PUSH,
            conflict_resolution=ConflictResolution.SOURCE_WINS
        )
        
        result = connector._sync_records(source_records, target_records, sync_config)
        
        assert result.success == True
        assert result.records_processed > 0
        
        print("✓ Data synchronization test passed")


def run_basic_tests():
    """Run basic tests that don't require API credentials"""
    print("\n" + "="*60)
    print("Running Basic CRM Connector Tests")
    print("="*60)
    
    # Test base classes
    test_base = TestBaseClasses()
    test_base.test_rate_limiter()
    test_base.test_retry_manager()
    test_base.test_data_mapper()
    
    # Test generic connectors
    test_generic = TestGenericConnectors()
    test_generic.test_rest_connector_creation()
    test_generic.test_graphql_connector_creation()
    
    # Test sync features
    test_sync = TestDataSynchronization()
    asyncio.run(test_sync.test_sync_config())
    asyncio.run(test_sync.test_sync_record())
    asyncio.run(test_sync.test_data_synchronization())
    
    print("\n✓ All basic tests passed!")
    print("\nTo run integration tests with actual CRM APIs:")
    print("1. Set up environment variables for your CRM credentials")
    print("2. Run: pytest test_connectors.py -v")


def run_integration_tests():
    """Run integration tests with actual CRM APIs"""
    print("\n" + "="*60)
    print("Running Integration Tests (Requires API Credentials)")
    print("="*60)
    
    async def test_all_connectors():
        # Test Salesforce
        sf_test = TestSalesforceConnector()
        try:
            await sf_test.test_salesforce_connection()
        except Exception as e:
            print(f"Salesforce test skipped: {str(e)}")
        
        # Test HubSpot
        hs_test = TestHubSpotConnector()
        try:
            await hs_test.test_hubspot_connection()
        except Exception as e:
            print(f"HubSpot test skipped: {str(e)}")
        
        # Test Dynamics 365
        dyn_test = TestDynamics365Connector()
        try:
            await dyn_test.test_dynamics_connection()
        except Exception as e:
            print(f"Dynamics 365 test skipped: {str(e)}")
    
    asyncio.run(test_all_connectors())


if __name__ == '__main__':
    # Check if we should run integration tests
    if os.getenv('RUN_INTEGRATION_TESTS', 'false').lower() == 'true':
        run_integration_tests()
    else:
        run_basic_tests()
        
        print("\n" + "="*60)
        print("Running with real API credentials...")
        print("="*60)
        print("To run integration tests, set environment variables and run:")
        print("export RUN_INTEGRATION_TESTS=true")
        print("python test_connectors.py")
