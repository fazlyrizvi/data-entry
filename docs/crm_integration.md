# CRM Integration Documentation

## Overview

The CRM Integration package provides secure API connectors for major CRM systems, enabling seamless integration and data synchronization between different CRM platforms and custom applications.

### Supported CRMs

- **Salesforce** (REST API, Bulk API)
- **HubSpot** (CRM API, Forms API)
- **Microsoft Dynamics 365** (Web API)
- **Generic REST APIs**
- **Generic GraphQL APIs**

### Key Features

- **OAuth 2.0 Authentication** - Secure authentication with all supported CRMs
- **Rate Limiting** - Built-in rate limiting to prevent API quota exhaustion
- **Retry Mechanisms** - Exponential backoff retry logic for failed requests
- **Data Mapping** - Flexible field mapping between internal and external formats
- **Bidirectional Synchronization** - Push, pull, and bidirectional data sync
- **Conflict Resolution** - Multiple conflict resolution strategies
- **Bulk Operations** - Efficient handling of large datasets
- **Error Handling** - Comprehensive error handling and logging
- **Async/Await Support** - Full asynchronous operation support

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Salesforce Connector](#salesforce-connector)
5. [HubSpot Connector](#hubspot-connector)
6. [Dynamics 365 Connector](#dynamics-365-connector)
7. [Generic Connectors](#generic-connectors)
8. [Data Synchronization](#data-synchronization)
9. [Field Mapping](#field-mapping)
10. [Error Handling](#error-handling)
11. [Examples](#examples)
12. [Best Practices](#best-practices)

## Installation

```bash
# Install required dependencies
pip install aiohttp asyncio
```

## Quick Start

### Basic Usage

```python
import asyncio
from crm_connectors import SalesforceConnector

async def main():
    # Configure Salesforce connector
    config = {
        'client_id': 'your_client_id',
        'client_secret': 'your_client_secret',
        'username': 'your_username',
        'password': 'your_password',
        'security_token': 'your_security_token',
        'instance_url': 'https://your-instance.salesforce.com'
    }
    
    # Initialize and authenticate
    connector = SalesforceConnector(config)
    await connector.authenticate()
    
    # Create a contact
    contact_data = {
        'FirstName': 'John',
        'LastName': 'Doe',
        'Email': 'john.doe@example.com'
    }
    
    result = await connector.create('Contact', contact_data)
    print(f"Created contact with ID: {result['id']}")
    
    # Close connection
    await connector.close()

asyncio.run(main())
```

### Multiple CRM Integration

```python
import asyncio
from crm_connectors import SalesforceConnector, HubSpotConnector

async def sync_crms():
    # Setup Salesforce
    salesforce_config = {
        'client_id': 'sf_client_id',
        'client_secret': 'sf_client_secret',
        'username': 'sf_username',
        'password': 'sf_password',
        'security_token': 'sf_security_token',
        'instance_url': 'https://sf-instance.salesforce.com'
    }
    
    # Setup HubSpot
    hubspot_config = {
        'client_id': 'hs_client_id',
        'client_secret': 'hs_client_secret',
        'access_token': 'hs_access_token',
        'portal_id': 'hs_portal_id'
    }
    
    # Initialize connectors
    sf_connector = SalesforceConnector(salesforce_config)
    hs_connector = HubSpotConnector(hubspot_config)
    
    # Authenticate both
    await sf_connector.authenticate()
    await hs_connector.authenticate()
    
    # Query from Salesforce
    sf_contacts = await sf_connector.query('Contact', {})
    
    # Sync to HubSpot
    sync_config = SyncConfig(
        direction=SyncDirection.PUSH,
        conflict_resolution=ConflictResolution.TIMESTAMP
    )
    
    result = await hs_connector.synchronize(sf_contacts, 'contacts', sync_config)
    print(f"Synced {result.records_succeeded} records")
    
    # Cleanup
    await sf_connector.close()
    await hs_connector.close()

asyncio.run(sync_crms())
```

## Configuration

### Common Configuration Parameters

All connectors support these common configuration options:

```python
config = {
    # Rate limiting
    'rate_limit': {
        'max_calls': 100,      # Max requests per time window
        'time_window': 60      # Time window in seconds
    },
    
    # Retry configuration
    'retry': {
        'max_retries': 3,      # Maximum retry attempts
        'base_delay': 1.0,     # Initial delay in seconds
        'max_delay': 60.0,     # Maximum delay in seconds
        'backoff_factor': 2.0  # Exponential backoff factor
    },
    
    # Field mappings
    'field_mappings': {
        'internal_field': 'external_field',
        'first_name': 'FirstName',
        'last_name': 'LastName'
    }
}
```

### Authentication Methods

#### OAuth 2.0 Password Flow (Salesforce)

```python
config = {
    'auth_method': 'password',
    'client_id': 'your_connected_app_client_id',
    'client_secret': 'your_connected_app_client_secret',
    'username': 'your_salesforce_username',
    'password': 'your_salesforce_password',
    'security_token': 'your_security_token',
    'instance_url': 'https://your-instance.salesforce.com'
}
```

#### OAuth 2.0 Client Credentials (Dynamics 365)

```python
config = {
    'tenant_id': 'your_azure_tenant_id',
    'client_id': 'your_azure_app_client_id',
    'client_secret': 'your_azure_app_client_secret',
    'resource_url': 'https://yourorg.crm.dynamics.com'
}
```

#### Bearer Token (HubSpot, Generic)

```python
config = {
    'access_token': 'your_oauth_access_token',
    'refresh_token': 'your_oauth_refresh_token',  # Optional
    'client_id': 'your_client_id',               # For token refresh
    'client_secret': 'your_client_secret'        # For token refresh
}
```

#### API Key Authentication

```python
config = {
    'base_url': 'https://api.example-crm.com',
    'auth_type': 'api_key',
    'auth_config': {
        'api_key': 'your_api_key',
        'key_header': 'X-API-Key'  # Default header
    }
}
```

#### Basic Authentication

```python
config = {
    'base_url': 'https://api.example-crm.com',
    'auth_type': 'basic',
    'auth_config': {
        'username': 'your_username',
        'password': 'your_password'
    }
}
```

## Salesforce Connector

### Features

- **REST API** - Standard CRUD operations
- **Bulk API** - Efficient handling of large datasets
- **SOQL Queries** - Advanced querying capabilities
- **Object Metadata** - Dynamic schema retrieval
- **Rate Limiting** - Automatic rate limit handling

### Configuration

```python
config = {
    'auth_method': 'password',  # or 'oauth'
    'client_id': 'your_connected_app_client_id',
    'client_secret': 'your_connected_app_client_secret',
    'username': 'your_salesforce_username',
    'password': 'your_salesforce_password',
    'security_token': 'your_security_token',
    'instance_url': 'https://your-instance.salesforce.com',
    'api_version': 'v58.0',           # Optional, defaults to v58.0
    'bulk_api_enabled': True,          # Enable Bulk API
    'bulk_api_version': 'v58.0'        # Bulk API version
}
```

### Usage Examples

#### Basic Operations

```python
from crm_connectors import SalesforceConnector

async def salesforce_operations():
    connector = SalesforceConnector(config)
    await connector.authenticate()
    
    # Create account
    account_data = {
        'Name': 'Acme Corporation',
        'Website': 'https://acme.com',
        'Industry': 'Technology'
    }
    account = await connector.create('Account', account_data)
    
    # Create contact associated with account
    contact_data = {
        'FirstName': 'Jane',
        'LastName': 'Smith',
        'Email': 'jane.smith@acme.com',
        'AccountId': account['id']
    }
    contact = await connector.create('Contact', contact_data)
    
    # Read record
    contact = await connector.read('Contact', contact['id'])
    
    # Update record
    update_data = {'Phone': '+1-555-0123'}
    await connector.update('Contact', contact['id'], update_data)
    
    # Query with filters
    contacts = await connector.query(
        entity_type='Contact',
        filters={
            'AccountId': account['id'],
            'Email': {'like': '@acme.com'}
        },
        fields=['Id', 'FirstName', 'LastName', 'Email'],
        limit=100
    )
    
    await connector.close()

asyncio.run(salesforce_operations())
```

#### Bulk Operations

```python
async def bulk_operations():
    connector = SalesforceConnector(config)
    await connector.authenticate()
    
    # Bulk create
    contacts = []
    for i in range(100):
        contacts.append({
            'FirstName': f'Contact{i+1}',
            'LastName': 'Bulk',
            'Email': f'contact{i+1}@example.com'
        })
    
    results = await connector.bulk_create('Contact', contacts, batch_size=25)
    print(f"Created {len(results)} contacts")
    
    # Bulk update
    updates = []
    for result in results[:50]:  # Update first 50
        if 'id' in result:
            updates.append({
                'id': result['id'],
                'LastName': 'Updated'
            })
    
    results = await connector.bulk_update('Contact', updates, batch_size=25)
    print(f"Updated {len(results)} contacts")
    
    # Bulk delete
    record_ids = [r.get('id') for r in results if 'id' in r]
    results = await connector.bulk_delete('Contact', record_ids, batch_size=25)
    print(f"Deleted {len(results)} contacts")
    
    await connector.close()

asyncio.run(bulk_operations())
```

#### SOQL Queries

```python
async def soql_queries():
    connector = SalesforceConnector(config)
    await connector.authenticate()
    
    # Complex SOQL query using the query method
    opportunities = await connector.query(
        entity_type='Opportunity',
        filters={
            'StageName': {'in': ['Prospecting', 'Qualification']},
            'Amount': {'gte': 10000},
            'CloseDate': {'gte': '2024-01-01'}
        },
        fields=[
            'Id', 'Name', 'Amount', 'StageName', 
            'CloseDate', 'Account.Name', 'Owner.Name'
        ],
        limit=50
    )
    
    for opp in opportunities:
        print(f"{opp['Name']}: ${opp['Amount']} - {opp['StageName']}")
    
    await connector.close()

asyncio.run(soql_queries())
```

## HubSpot Connector

### Features

- **CRM API** - Contact, Company, Deal management
- **Forms API** - Form submission capabilities
- **Batch Operations** - Efficient bulk processing
- **Rate Limiting** - Automatic rate limit handling
- **Property Management** - Dynamic property retrieval

### Configuration

```python
config = {
    'client_id': 'your_hubspot_app_client_id',
    'client_secret': 'your_hubspot_app_client_secret',
    'access_token': 'your_hubspot_access_token',
    'refresh_token': 'your_hubspot_refresh_token',  # Optional
    'portal_id': 'your_hubspot_portal_id',
    'api_url': 'https://api.hubapi.com',  # Default
    'rate_limit': {
        'max_calls': 100,
        'time_window': 60
    }
}
```

### Usage Examples

#### Contact Management

```python
from crm_connectors import HubSpotConnector

async def contact_management():
    connector = HubSpotConnector(config)
    await connector.authenticate()
    
    # Create contact
    contact_data = {
        'email': 'john.doe@example.com',
        'firstname': 'John',
        'lastname': 'Doe',
        'phone': '+1-555-0123'
    }
    
    contact = await connector.create('contacts', contact_data)
    
    # Read contact
    contact = await connector.read('contacts', contact['id'])
    
    # Update contact
    update_data = {'lastname': 'Smith'}
    await connector.update('contacts', contact['id'], update_data)
    
    # Query contacts
    contacts = await connector.query(
        entity_type='contacts',
        filters={
            'email': {'like': '@example.com'},
            'createdate': {'gte': '2024-01-01'}
        },
        fields=['id', 'email', 'firstname', 'lastname'],
        limit=50
    )
    
    await connector.close()

asyncio.run(contact_management())
```

#### Company and Deal Management

```python
async def company_deal_management():
    connector = HubSpotConnector(config)
    await connector.authenticate()
    
    # Create company
    company_data = {
        'name': 'Acme Corporation',
        'domain': 'acme.com',
        'industry': 'Technology'
    }
    company = await connector.create('companies', company_data)
    
    # Create deal
    deal_data = {
        'dealname': 'Enterprise License',
        'amount': 50000,
        'dealstage': 'appointmentscheduled',
        'pipeline': 'default',
        'closedate': '2024-12-31'
    }
    deal = await connector.create('deals', deal_data)
    
    # Associate deal with company (HubSpot specific)
    # Note: This would require the association endpoint
    
    await connector.close()

asyncio.run(company_deal_management())
```

#### Form Submission

```python
async def form_submission():
    connector = HubSpotConnector(config)
    await connector.authenticate()
    
    # Get available forms
    forms = await connector.get_forms()
    print(f"Available forms: {len(forms)}")
    
    # Submit form
    form_data = {
        'email': 'visitor@example.com',
        'firstname': 'Website',
        'lastname': 'Visitor',
        'message': 'Interested in your services'
    }
    
    # Submit to specific form
    result = await connector.submit_form(
        form_id='your_form_id',
        data=form_data,
        portal_id='your_portal_id'
    )
    
    print(f"Form submitted: {result}")
    
    await connector.close()

asyncio.run(form_submission())
```

## Dynamics 365 Connector

### Features

- **Web API** - Full CRUD operations
- **OData Queries** - Advanced querying with OData
- **Entity Relationships** - Association and dissociation
- **Functions** - Execute custom functions
- **Metadata** - Dynamic schema retrieval

### Configuration

```python
config = {
    'tenant_id': 'your_azure_tenant_id',
    'client_id': 'your_azure_app_client_id',
    'client_secret': 'your_azure_app_client_secret',
    'resource_url': 'https://yourorg.crm.dynamics.com',
    'api_version': '9.2',  # Optional, defaults to 9.2
    'scope': 'https://yourorg.crm.dynamics.com/.default'
}
```

### Usage Examples

#### Basic Operations

```python
from crm_connectors import Dynamics365Connector

async def dynamics_operations():
    connector = Dynamics365Connector(config)
    await connector.authenticate()
    
    # Create account
    account_data = {
        'name': 'Contoso Ltd',
        'websiteurl': 'https://contoso.com',
        'industrycode': 1  # Technology
    }
    
    account = await connector.create('accounts', account_data)
    
    # Create contact
    contact_data = {
        'firstname': 'Alice',
        'lastname': 'Johnson',
        'emailaddress1': 'alice@contoso.com',
        'parentcustomerid': account['id']  # Associate with account
    }
    
    contact = await connector.create('contacts', contact_data)
    
    # Query with filters
    contacts = await connector.query(
        entity_type='contacts',
        filters={
            'emailaddress1': {'like': '@contoso.com'},
            'createdon': {'gte': '2024-01-01'}
        },
        fields=['contactid', 'firstname', 'lastname', 'emailaddress1'],
        limit=100
    )
    
    await connector.close()

asyncio.run(dynamics_operations())
```

#### Entity Relationships

```python
async def entity_relationships():
    connector = Dynamics365Connector(config)
    await connector.authenticate()
    
    # Associate contact with account
    await connector.associate_entities(
        entity_type='contacts',
        entity_id='contact_guid',
        related_entity_type='accounts',
        related_entity_id='account_guid',
        relationship_name='contact_customer_accounts'  # Relationship name
    )
    
    # Disassociate entities
    await connector.disassociate_entities(
        entity_type='contacts',
        entity_id='contact_guid',
        related_entity_type='accounts',
        related_entity_id='account_guid',
        relationship_name='contact_customer_accounts'
    )
    
    await connector.close()

asyncio.run(entity_relationships())
```

#### Execute Functions

```python
async def execute_functions():
    connector = Dynamics365Connector(config)
    await connector.authenticate()
    
    # Execute WhoAmI function
    whoami = await connector.who_am_i()
    print(f"User ID: {whoami.get('UserId')}")
    print(f"Organization ID: {whoami.get('OrganizationId')}")
    
    # Execute custom function (example)
    # result = await connector.execute_function(
    #     'YourCustomFunction',
    #     params={'param1': 'value1', 'param2': 123}
    # )
    
    await connector.close()

asyncio.run(execute_functions())
```

## Generic Connectors

### Generic REST Connector

For connecting to any REST API with configurable endpoints:

```python
from crm_connectors import RestConnector

config = {
    'base_url': 'https://api.example-crm.com/v1',
    'auth_type': 'bearer',  # bearer, basic, api_key, oauth2
    'auth_config': {
        'token': 'your_api_token'
    },
    'headers': {
        'User-Agent': 'CRM-Integration/1.0'
    },
    'endpoints': {
        'create': '/{entity_type}',                    # POST
        'read': '/{entity_type}/{id}',                # GET
        'update': '/{entity_type}/{id}',              # PUT
        'delete': '/{entity_type}/{id}',              # DELETE
        'query': '/{entity_type}'                      # GET with params
    },
    'timeout': 30,
    'supported_entities': ['contacts', 'companies', 'deals']
}

connector = RestConnector(config)
await connector.authenticate()
```

### Generic GraphQL Connector

For connecting to GraphQL APIs:

```python
from crm_connectors import GraphQLConnector

config = {
    'endpoint': 'https://api.example-crm.com/graphql',
    'auth_type': 'bearer',
    'auth_config': {
        'token': 'your_graphql_token'
    },
    'supported_entities': ['contacts', 'companies', 'deals']
}

connector = GraphQLConnector(config)
await connector.authenticate()

# The GraphQL connector automatically generates queries and mutations
# based on the entity type
```

## Data Synchronization

### Sync Configuration

```python
from crm_connectors import SyncConfig, SyncDirection, ConflictResolution

config = SyncConfig(
    direction=SyncDirection.BIDIRECTIONAL,     # PUSH, PULL, or BIDIRECTIONAL
    conflict_resolution=ConflictResolution.TIMESTAMP,  # TIMESTAMP, SOURCE_WINS, TARGET_WINS, CUSTOM
    batch_size=100,                            # Records per batch
    max_retries=3,                             # Max retry attempts
    retry_delay=1.0,                           # Initial retry delay
    parallel_operations=5,                     # Concurrent operations
    custom_resolver=my_custom_resolver,        # Custom conflict resolution
    include_metadata=True                      # Include metadata in sync
)
```

### Conflict Resolution Strategies

#### Timestamp-based (Default)

```python
config = SyncConfig(
    conflict_resolution=ConflictResolution.TIMESTAMP
)
# Most recent record (by timestamp) wins
```

#### Source/Target Wins

```python
config = SyncConfig(
    conflict_resolution=ConflictResolution.SOURCE_WINS
)
# or
config = SyncConfig(
    conflict_resolution=ConflictResolution.TARGET_WINS
)
```

#### Custom Resolution

```python
def custom_conflict_resolver(source_record, target_record):
    # Custom logic to resolve conflicts
    # Return True to use source, False to use target
    if source_record.data.get('priority') > target_record.data.get('priority'):
        return True  # Use source record
    return False  # Use target record

config = SyncConfig(
    conflict_resolution=ConflictResolution.CUSTOM,
    custom_resolver=custom_conflict_resolver
)
```

### Synchronization Example

```python
async def synchronize_data():
    source_connector = SalesforceConnector(salesforce_config)
    target_connector = HubSpotConnector(hubspot_config)
    
    await source_connector.authenticate()
    await target_connector.authenticate()
    
    # Get data from source
    source_contacts = await source_connector.query('Contact', {})
    
    # Configure synchronization
    sync_config = SyncConfig(
        direction=SyncDirection.PUSH,
        conflict_resolution=ConflictResolution.TIMESTAMP,
        batch_size=50,
        custom_resolver=my_custom_resolver
    )
    
    # Perform synchronization
    result = await target_connector.synchronize(
        source_data=source_contacts,
        target_entity='contacts',
        config=sync_config
    )
    
    print(f"Synchronization Results:")
    print(f"  - Records processed: {result.records_processed}")
    print(f"  - Successful: {result.records_succeeded}")
    print(f"  - Failed: {result.records_failed}")
    print(f"  - Conflicts: {len(result.conflicts)}")
    print(f"  - Execution time: {result.execution_time:.2f}s")
    
    # Handle conflicts
    for conflict in result.conflicts:
        print(f"Conflict in record {conflict['record_id']}:")
        print(f"  Source: {conflict['source']}")
        print(f"  Target: {conflict['target']}")
    
    await source_connector.close()
    await target_connector.close()

asyncio.run(synchronize_data())
```

## Field Mapping

### Basic Field Mapping

```python
# Configure field mappings in connector
config = {
    'field_mappings': {
        # Internal field -> External field
        'first_name': 'FirstName',           # Salesforce
        'last_name': 'LastName',             # Salesforce
        'email': 'Email',                    # Salesforce
        
        # Or for HubSpot
        'first_name': 'firstname',
        'last_name': 'lastname',
        'email': 'email',
        
        # Or for Dynamics 365
        'first_name': 'firstname',
        'last_name': 'lastname',
        'email': 'emailaddress1'
    }
}

connector = SalesforceConnector(config)
await connector.authenticate()

# Add field mapping dynamically
connector.data_mapper.add_mapping('middle_name', 'MiddleName')

# Remove field mapping
connector.data_mapper.remove_mapping('middle_name')
```

### Data Transformation

```python
from crm_connectors.utils import ConversionHelper

# Normalize phone numbers
phone = '+1 (555) 123-4567'
normalized_phone = ConversionHelper.normalize_phone(phone)
# Result: '+15551234567'

# Normalize email
email = 'John.Doe@Example.COM'
normalized_email = ConversionHelper.normalize_email(email)
# Result: 'john.doe@example.com'

# Convert data types
number = ConversionHelper.to_number('123.45')
# Result: 123.45

boolean = ConversionHelper.to_boolean('true')
# Result: True

date = ConversionHelper.to_date('2024-01-15')
# Result: datetime.date(2024, 1, 15)
```

### Field Mapping Helper

```python
from crm_connectors.utils import FieldMappingHelper

# Get standard mappings for specific CRM
salesforce_mappings = FieldMappingHelper.get_crm_mappings('salesforce')
hubspot_mappings = FieldMappingHelper.get_crm_mappings('hubspot')
dynamics_mappings = FieldMappingHelper.get_crm_mappings('dynamics365')

# Create mapping function
map_function = FieldMappingHelper.create_mapping_function(salesforce_mappings)

# Apply mappings
data = {'first_name': 'John', 'last_name': 'Doe', 'email': 'john@example.com'}
mapped_data = map_function(data)
# Result: {'FirstName': 'John', 'LastName': 'Doe', 'Email': 'john@example.com'}
```

## Error Handling

### Built-in Error Handling

All connectors include comprehensive error handling:

```python
from crm_connectors.utils import ErrorHandler

try:
    result = await connector.create('Contact', contact_data)
except ValueError as e:
    # Invalid input data
    print(f"Validation error: {e}")
except PermissionError as e:
    # Authentication/authorization error
    print(f"Permission error: {e}")
except FileNotFoundError as e:
    # Record not found
    print(f"Record not found: {e}")
except ConnectionError as e:
    # Network/server error
    print(f"Connection error: {e}")
except Exception as e:
    # Generic error
    print(f"Unexpected error: {e}")
```

### Retry Decorator

```python
from crm_connectors.utils import ErrorHandler

@ErrorHandler.retry_on_failure(max_retries=3, delay=1.0, backoff_factor=2.0)
async def unstable_operation():
    result = await connector.query('Contact', {})
    return result

# This will automatically retry on failure
result = await unstable_operation()
```

### Safe Data Access

```python
from crm_connectors.utils import ErrorHandler

# Safe nested dictionary access
data = {
    'contact': {
        'address': {
            'city': 'New York'
        }
    }
}

# Safe access with default value
city = ErrorHandler.safe_get_nested(data, 'contact.address.city', 'Unknown')
# Result: 'New York'

# Safe access to non-existent path
country = ErrorHandler.safe_get_nested(data, 'contact.address.country', 'USA')
# Result: 'USA'
```

## Examples

### Complete Integration Example

```python
import asyncio
from crm_connectors import (
    SalesforceConnector, 
    HubSpotConnector,
    SyncConfig,
    SyncDirection,
    ConflictResolution
)

async def complete_integration():
    """Complete example integrating Salesforce and HubSpot"""
    
    # Configuration
    salesforce_config = {
        'client_id': 'your_sf_client_id',
        'client_secret': 'your_sf_client_secret',
        'username': 'your_sf_username',
        'password': 'your_sf_password',
        'security_token': 'your_sf_security_token',
        'instance_url': 'https://your-instance.salesforce.com',
        'rate_limit': {'max_calls': 100, 'time_window': 60}
    }
    
    hubspot_config = {
        'client_id': 'your_hs_client_id',
        'client_secret': 'your_hs_client_secret',
        'access_token': 'your_hs_access_token',
        'portal_id': 'your_hs_portal_id',
        'rate_limit': {'max_calls': 100, 'time_window': 60}
    }
    
    # Initialize connectors
    sf_connector = SalesforceConnector(salesforce_config)
    hs_connector = HubSpotConnector(hubspot_config)
    
    try:
        # Authenticate
        print("Authenticating with Salesforce...")
        await sf_connector.authenticate()
        
        print("Authenticating with HubSpot...")
        await hs_connector.authenticate()
        
        # Test connections
        sf_test = await sf_connector.test_connection()
        hs_test = await hs_connector.test_connection()
        
        print(f"Salesforce connection: {sf_test['success']}")
        print(f"HubSpot connection: {hs_test['success']}")
        
        # Set up field mappings
        sf_connector.data_mapper.add_mapping('first_name', 'FirstName')
        sf_connector.data_mapper.add_mapping('last_name', 'LastName')
        sf_connector.data_mapper.add_mapping('email', 'Email')
        sf_connector.data_mapper.add_mapping('phone', 'Phone')
        
        hs_connector.data_mapper.add_mapping('first_name', 'firstname')
        hs_connector.data_mapper.add_mapping('last_name', 'lastname')
        hs_connector.data_mapper.add_mapping('email', 'email')
        hs_connector.data_mapper.add_mapping('phone', 'phone')
        
        # Query Salesforce contacts
        print("Fetching contacts from Salesforce...")
        sf_contacts = await sf_connector.query(
            entity_type='Contact',
            filters={'Email': {'ne': None}},  # Only contacts with email
            fields=['Id', 'FirstName', 'LastName', 'Email', 'Phone'],
            limit=100
        )
        
        print(f"Found {len(sf_contacts)} contacts in Salesforce")
        
        # Create test data if no contacts exist
        if not sf_contacts:
            print("Creating test contacts...")
            test_contacts = []
            for i in range(5):
                contact_data = {
                    'FirstName': f'Test{i+1}',
                    'LastName': 'Contact',
                    'Email': f'test{i+1}@example.com',
                    'Phone': f'+1-555-{1000+i}'
                }
                created = await sf_connector.create('Contact', contact_data)
                test_contacts.append(created)
            
            sf_contacts = await sf_connector.query(
                entity_type='Contact',
                filters={'Email': {'like': '@example.com'}},
                fields=['Id', 'FirstName', 'LastName', 'Email', 'Phone']
            )
            print(f"Created and fetched {len(sf_contacts)} test contacts")
        
        # Sync to HubSpot
        sync_config = SyncConfig(
            direction=SyncDirection.PUSH,
            conflict_resolution=ConflictResolution.TIMESTAMP,
            batch_size=10
        )
        
        print(f"Syncing {len(sf_contacts)} contacts to HubSpot...")
        sync_result = await hs_connector.synchronize(
            source_data=sf_contacts,
            target_entity='contacts',
            config=sync_config
        )
        
        print(f"Sync Results:")
        print(f"  - Processed: {sync_result.records_processed}")
        print(f"  - Successful: {sync_result.records_succeeded}")
        print(f"  - Failed: {sync_result.records_failed}")
        print(f"  - Conflicts: {len(sync_result.conflicts)}")
        print(f"  - Time: {sync_result.execution_time:.2f}s")
        
        # Verify sync by querying HubSpot
        hs_contacts = await hs_connector.query(
            entity_type='contacts',
            filters={},
            fields=['id', 'email', 'firstname', 'lastname'],
            limit=100
        )
        
        print(f"HubSpot now has {len(hs_contacts)} contacts")
        
        # Demonstrate bulk operations
        if len(sf_contacts) > 0:
            print("Testing bulk operations...")
            
            # Bulk update test - add "Synced from Salesforce" to notes
            updates = []
            for contact in sf_contacts[:3]:  # Update first 3
                updates.append({
                    'id': contact['Id'],
                    'Description': 'Updated via bulk operation'
                })
            
            if updates:
                bulk_results = await sf_connector.bulk_update('Contact', updates, batch_size=2)
                print(f"Bulk updated {len(bulk_results)} records")
        
        # Demonstrate bidirectional sync
        print("Testing bidirectional sync...")
        
        # Add some new contacts to HubSpot
        new_hs_contacts = []
        for i in range(3):
            contact_data = {
                'email': f'new{i+1}@hubspot.com',
                'firstname': f'New{i+1}',
                'lastname': 'HubSpot',
                'phone': f'+1-555-{2000+i}'
            }
            created = await hs_connector.create('contacts', contact_data)
            new_hs_contacts.append(created)
        
        # Sync back to Salesforce
        sync_config_bidirectional = SyncConfig(
            direction=SyncDirection.BIDIRECTIONAL,
            conflict_resolution=ConflictResolution.TIMESTAMP
        )
        
        bidirectional_result = await sf_connector.synchronize(
            source_data=new_hs_contacts,
            target_entity='Contact',
            config=sync_config_bidirectional
        )
        
        print(f"Bidirectional sync completed:")
        print(f"  - Processed: {bidirectional_result.records_processed}")
        print(f"  - Successful: {bidirectional_result.records_succeeded}")
        
        print("\n✓ Integration example completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Integration failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print("Closing connections...")
        await sf_connector.close()
        await hs_connector.close()
        print("✓ Connections closed")

# Run the example
if __name__ == '__main__':
    asyncio.run(complete_integration())
```

### Cross-Platform Data Migration

```python
async def migrate_data():
    """Migrate data from one CRM to another with data transformation"""
    
    # Source: Salesforce
    source_config = {
        'client_id': 'source_client_id',
        'client_secret': 'source_client_secret',
        'username': 'source_username',
        'password': 'source_password',
        'security_token': 'source_security_token',
        'instance_url': 'https://source-instance.salesforce.com'
    }
    
    # Target: HubSpot
    target_config = {
        'client_id': 'target_client_id',
        'client_secret': 'target_client_secret',
        'access_token': 'target_access_token',
        'portal_id': 'target_portal_id'
    }
    
    source_connector = SalesforceConnector(source_config)
    target_connector = HubSpotConnector(target_config)
    
    await source_connector.authenticate()
    await target_connector.authenticate()
    
    # Query all accounts from source
    accounts = await source_connector.query('Account', {})
    
    # Transform data for target
    transformed_accounts = []
    for account in accounts:
        transformed = {
            'name': account.get('Name', ''),
            'domain': account.get('Website', '').replace('https://', '').replace('http://', ''),
            'industry': account.get('Industry', ''),
            'phone': account.get('Phone', ''),
            'description': f"Migrated from Salesforce - Account ID: {account.get('Id')}"
        }
        transformed_accounts.append(transformed)
    
    # Bulk create in target
    results = await target_connector.bulk_create('companies', transformed_accounts, batch_size=50)
    
    print(f"Migrated {len(results)} accounts from Salesforce to HubSpot")
    
    await source_connector.close()
    await target_connector.close()

asyncio.run(migrate_data())
```

### Real-time Data Sync

```python
async def real_time_sync():
    """Set up real-time synchronization between CRMs"""
    
    import asyncio
    import time
    
    # Configuration
    source_config = {...}  # Salesforce config
    target_config = {...}  # HubSpot config
    
    source_connector = SalesforceConnector(source_config)
    target_connector = HubSpotConnector(target_config)
    
    await source_connector.authenticate()
    await target_connector.authenticate()
    
    last_sync_time = datetime.utcnow()
    
    async def sync_loop():
        nonlocal last_sync_time
        
        while True:
            try:
                # Query for records modified since last sync
                filters = {
                    'LastModifiedDate': {'gte': last_sync_time.isoformat()}
                }
                
                modified_records = await source_connector.query(
                    entity_type='Contact',
                    filters=filters,
                    fields=['Id', 'FirstName', 'LastName', 'Email', 'Phone', 'LastModifiedDate']
                )
                
                if modified_records:
                    # Sync to target
                    sync_config = SyncConfig(
                        direction=SyncDirection.PUSH,
                        conflict_resolution=ConflictResolution.TIMESTAMP
                    )
                    
                    result = await target_connector.synchronize(
                        source_data=modified_records,
                        target_entity='contacts',
                        config=sync_config
                    )
                    
                    print(f"Synced {len(modified_records)} modified records")
                
                # Update last sync time
                last_sync_time = datetime.utcnow()
                
                # Wait before next sync
                await asyncio.sleep(60)  # Sync every minute
                
            except Exception as e:
                print(f"Sync error: {str(e)}")
                await asyncio.sleep(60)  # Wait before retry
    
    # Start sync loop
    sync_task = asyncio.create_task(sync_loop())
    
    try:
        # Keep running for demo purposes
        await asyncio.sleep(300)  # Run for 5 minutes
    except KeyboardInterrupt:
        print("Stopping sync...")
    finally:
        sync_task.cancel()
        await source_connector.close()
        await target_connector.close()

asyncio.run(real_time_sync())
```

## Best Practices

### 1. Configuration Management

```python
import os
from dataclasses import dataclass

@dataclass
class CRMConfig:
    """Centralized configuration management"""
    salesforce: dict
    hubspot: dict
    dynamics: dict
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        return cls(
            salesforce={
                'client_id': os.getenv('SF_CLIENT_ID'),
                'client_secret': os.getenv('SF_CLIENT_SECRET'),
                'username': os.getenv('SF_USERNAME'),
                'password': os.getenv('SF_PASSWORD'),
                'security_token': os.getenv('SF_SECURITY_TOKEN'),
                'instance_url': os.getenv('SF_INSTANCE_URL')
            },
            hubspot={
                'client_id': os.getenv('HS_CLIENT_ID'),
                'client_secret': os.getenv('HS_CLIENT_SECRET'),
                'access_token': os.getenv('HS_ACCESS_TOKEN'),
                'portal_id': os.getenv('HS_PORTAL_ID')
            },
            dynamics={
                'tenant_id': os.getenv('DYN_TENANT_ID'),
                'client_id': os.getenv('DYN_CLIENT_ID'),
                'client_secret': os.getenv('DYN_CLIENT_SECRET'),
                'resource_url': os.getenv('DYN_RESOURCE_URL')
            }
        )

config = CRMConfig.from_env()
```

### 2. Connection Pooling

```python
class CRMManager:
    """Manage multiple CRM connections with pooling"""
    
    def __init__(self, configs: dict):
        self.connectors = {}
        self.configs = configs
    
    async def get_connector(self, crm_type: str):
        """Get or create connector"""
        if crm_type not in self.connectors:
            if crm_type == 'salesforce':
                self.connectors[crm_type] = SalesforceConnector(self.configs[crm_type])
            elif crm_type == 'hubspot':
                self.connectors[crm_type] = HubSpotConnector(self.configs[crm_type])
            elif crm_type == 'dynamics':
                self.connectors[crm_type] = Dynamics365Connector(self.configs[crm_type])
        
        connector = self.connectors[crm_type]
        if not connector.access_token:
            await connector.authenticate()
        
        return connector
    
    async def close_all(self):
        """Close all connections"""
        for connector in self.connectors.values():
            await connector.close()

# Usage
manager = CRMManager(configs)
sf_connector = await manager.get_connector('salesforce')
hs_connector = await manager.get_connector('hubspot')
```

### 3. Error Recovery

```python
async def robust_operation(attempts: int = 3):
    """Robust operation with circuit breaker pattern"""
    
    for attempt in range(attempts):
        try:
            result = await connector.query('Contact', {})
            return result
        except ConnectionError:
            if attempt < attempts - 1:
                # Reconnect and retry
                await connector.authenticate()
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
        except PermissionError:
            # Authentication issue - cannot recover
            raise
        except Exception as e:
            if attempt < attempts - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            raise
    
    raise Exception("Max attempts reached")
```

### 4. Data Validation

```python
from crm_connectors.utils import DataValidator

async def validated_create(connector, entity_type: str, data: dict):
    """Create record with validation"""
    
    # Validate required fields
    required_fields = get_required_fields(entity_type)
    missing = DataValidator.validate_required_fields(data, required_fields)
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
    
    # Validate email format
    if 'email' in data:
        if not DataValidator.validate_email(data['email']):
            raise ValueError("Invalid email format")
    
    # Validate phone format
    if 'phone' in data:
        if not DataValidator.validate_phone(data['phone']):
            raise ValueError("Invalid phone format")
    
    # Sanitize string fields
    for field in ['first_name', 'last_name', 'company']:
        if field in data:
            data[field] = DataValidator.sanitize_string(data[field], max_length=255)
    
    return await connector.create(entity_type, data)
```

### 5. Monitoring and Logging

```python
import logging
from crm_connectors.utils import LoggingConfig

# Configure logging
LoggingConfig.setup_logging(
    level='INFO',
    log_file='crm_integration.log',
    format_string='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)

logger = logging.getLogger(__name__)

class MonitoredConnector(BaseCRMConnector):
    """Connector with monitoring and metrics"""
    
    async def create(self, entity_type: str, data: dict):
        start_time = time.time()
        logger.info(f"Creating {entity_type} record")
        
        try:
            result = await super().create(entity_type, data)
            duration = time.time() - start_time
            logger.info(f"Successfully created {entity_type} record in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Failed to create {entity_type} record after {duration:.2f}s: {str(e)}")
            raise
```

### 6. Batch Processing

```python
async def process_large_dataset(connector, entity_type: str, data_source):
    """Process large datasets with proper batching"""
    
    batch_size = 50
    processed = 0
    errors = []
    
    # Convert to batches
    for i in range(0, len(data_source), batch_size):
        batch = data_source[i:i + batch_size]
        
        try:
            # Process batch
            results = await connector.bulk_create(entity_type, batch, batch_size=batch_size)
            
            # Count successes and failures
            batch_success = sum(1 for r in results if r.get('success'))
            batch_failures = len(results) - batch_success
            
            processed += batch_success
            errors.extend([r for r in results if not r.get('success')])
            
            logger.info(f"Batch {i//batch_size + 1}: {batch_success} success, {batch_failures} failures")
            
            # Check for critical failures
            if batch_failures == len(batch):
                logger.error(f"Batch {i//batch_size + 1} completely failed")
            
        except Exception as e:
            logger.error(f"Batch {i//batch_size + 1} error: {str(e)}")
            errors.append({'batch': i//batch_size + 1, 'error': str(e)})
    
    return {'processed': processed, 'errors': errors}
```

### 7. Security Best Practices

```python
# Never hardcode credentials
config = {
    'client_id': os.getenv('CRM_CLIENT_ID'),  # Use environment variables
    'client_secret': os.getenv('CRM_CLIENT_SECRET'),
    # ...
}

# Validate configuration
from crm_connectors.utils import ConfigValidator

errors = ConfigValidator.validate_salesforce_config(config)
if errors:
    raise ValueError(f"Invalid configuration: {errors}")

# Use HTTPS only
if not config['instance_url'].startswith('https://'):
    raise ValueError("Only HTTPS connections are allowed")

# Implement rate limiting awareness
async def rate_limit_aware_operation(connector, operation, *args, **kwargs):
    """Operation that respects rate limits"""
    if hasattr(connector, '_rate_limit_remaining'):
        if connector._rate_limit_remaining < 10:
            wait_time = connector._rate_limit_reset - time.time()
            if wait_time > 0:
                logger.warning(f"Rate limit approaching, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
    
    return await operation(*args, **kwargs)
```

## Troubleshooting

### Common Issues

#### 1. Authentication Failures

```
Error: "Authentication failed: 401 - Unauthorized"
```

**Solutions:**
- Verify credentials are correct
- Check if security tokens have expired
- Ensure the application has proper permissions
- Verify the instance URLs are correct

#### 2. Rate Limit Exceeded

```
Error: "Rate limit exceeded: 429"
```

**Solutions:**
- Implement exponential backoff
- Reduce batch sizes
- Use bulk APIs when available
- Monitor rate limit headers

#### 3. Field Mapping Errors

```
Error: "Field 'InvalidField' not found in target schema"
```

**Solutions:**
- Check field names match the target CRM schema
- Verify field mappings are correct
- Use describe/entity metadata endpoints to get field names

#### 4. Data Type Mismatches

```
Error: "Field 'Phone' should be string, got int"
```

**Solutions:**
- Validate data types before sending
- Use conversion helpers to normalize data
- Check API documentation for expected data types

#### 5. Network/Connection Issues

```
Error: "Connection timeout after 30 seconds"
```

**Solutions:**
- Increase timeout values
- Check network connectivity
- Implement retry logic with exponential backoff
- Use connection pooling

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
from crm_connectors.utils import LoggingConfig

# Enable debug logging
LoggingConfig.setup_logging(level='DEBUG')

# Or set specific logger levels
logging.getLogger('crm_connectors').setLevel(logging.DEBUG)
```

### Connection Testing

Use the built-in connection testing:

```python
# Test all configured connectors
configs = {
    'salesforce': salesforce_config,
    'hubspot': hubspot_config,
    'dynamics': dynamics_config
}

for name, config in configs.items():
    connector = create_connector(name, config)
    try:
        result = await connector.test_connection()
        print(f"{name}: {result}")
    except Exception as e:
        print(f"{name}: Failed - {str(e)}")
    finally:
        await connector.close()
```

## API Reference

### BaseCRMConnector

Base class for all CRM connectors.

#### Methods

- `authenticate() -> bool` - Authenticate with the CRM
- `create(entity_type, data) -> Dict[str, Any]` - Create a record
- `read(entity_type, entity_id) -> Dict[str, Any]` - Read a record
- `update(entity_type, entity_id, data) -> Dict[str, Any]` - Update a record
- `delete(entity_type, entity_id) -> bool` - Delete a record
- `query(entity_type, filters, fields, limit) -> List[Dict[str, Any]]` - Query records
- `bulk_create(entity_type, records, batch_size) -> List[Dict[str, Any]]` - Bulk create
- `bulk_update(entity_type, updates, batch_size) -> List[Dict[str, Any]]` - Bulk update
- `synchronize(source_data, target_entity, config) -> SyncResult` - Synchronize data
- `test_connection() -> Dict[str, Any]` - Test connection
- `close()` - Close connector

### SyncConfig

Configuration for synchronization operations.

#### Parameters

- `direction: SyncDirection` - Sync direction (PUSH, PULL, BIDIRECTIONAL)
- `conflict_resolution: ConflictResolution` - Conflict resolution strategy
- `batch_size: int` - Batch size for operations
- `max_retries: int` - Maximum retry attempts
- `retry_delay: float` - Initial retry delay
- `custom_resolver: Optional[Callable]` - Custom conflict resolver
- `field_mappings: Dict[str, str]` - Field mapping dictionary
- `include_metadata: bool` - Include metadata in sync
- `parallel_operations: int` - Concurrent operations
- `timeout: int` - Operation timeout

### SyncResult

Result of synchronization operation.

#### Attributes

- `success: bool` - Whether sync was successful
- `records_processed: int` - Number of records processed
- `records_succeeded: int` - Number of successful operations
- `records_failed: int` - Number of failed operations
- `conflicts: List[Dict[str, Any]]` - List of conflicts
- `errors: List[str]` - List of errors
- `metadata: Dict[str, Any]` - Additional metadata
- `execution_time: float` - Execution time in seconds

## Support and Contributing

For issues, questions, or contributions:

1. Check the documentation and examples
2. Review the troubleshooting section
3. Check existing issues in the repository
4. Create a new issue with detailed information

## License

This CRM Integration package is provided under the MIT License.
