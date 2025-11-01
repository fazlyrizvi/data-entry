# CRM API Connectors

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](docs/crm_integration.md)

A comprehensive, enterprise-grade CRM integration library supporting Salesforce, HubSpot, Microsoft Dynamics 365, and generic REST/GraphQL APIs.

## 🚀 Features

- **Multi-CRM Support**: Salesforce (REST/Bulk API), HubSpot (CRM/Forms API), Dynamics 365 (Web API)
- **OAuth 2.0 Authentication**: Secure authentication for all supported CRMs
- **Bidirectional Synchronization**: Push, pull, and bidirectional data sync with conflict resolution
- **Rate Limiting**: Built-in rate limiting to prevent API quota exhaustion
- **Retry Mechanisms**: Exponential backoff retry logic with configurable parameters
- **Data Mapping**: Flexible field mapping between internal and external formats
- **Bulk Operations**: Efficient handling of large datasets with batch processing
- **Async/Await**: Full asynchronous operation support for high performance
- **Error Handling**: Comprehensive error handling and logging
- **Generic Connectors**: Support for custom REST and GraphQL APIs

## 📦 Installation

```bash
pip install -r requirements.txt
```

Or install core dependencies only:
```bash
pip install aiohttp asyncio
```

## 🔧 Quick Start

### Basic Salesforce Integration

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

### Cross-CRM Synchronization

```python
import asyncio
from crm_connectors import (
    SalesforceConnector, 
    HubSpotConnector,
    SyncConfig,
    SyncDirection,
    ConflictResolution
)

async def sync_example():
    # Setup connectors
    sf_config = {
        'client_id': 'sf_client_id',
        'client_secret': 'sf_client_secret',
        'username': 'sf_username',
        'password': 'sf_password',
        'security_token': 'sf_security_token',
        'instance_url': 'https://sf-instance.salesforce.com'
    }
    
    hs_config = {
        'client_id': 'hs_client_id',
        'client_secret': 'hs_client_secret',
        'access_token': 'hs_access_token',
        'portal_id': 'hs_portal_id'
    }
    
    # Initialize connectors
    sf_connector = SalesforceConnector(sf_config)
    hs_connector = HubSpotConnector(hs_config)
    
    # Authenticate
    await sf_connector.authenticate()
    await hs_connector.authenticate()
    
    # Get Salesforce contacts
    sf_contacts = await sf_connector.query('Contact', {})
    
    # Configure synchronization
    sync_config = SyncConfig(
        direction=SyncDirection.PUSH,
        conflict_resolution=ConflictResolution.TIMESTAMP,
        batch_size=50
    )
    
    # Sync to HubSpot
    result = await hs_connector.synchronize(sf_contacts, 'contacts', sync_config)
    print(f"Synced {result.records_succeeded} records")
    
    # Cleanup
    await sf_connector.close()
    await hs_connector.close()

asyncio.run(sync_example())
```

## 📚 Supported CRMs

| CRM | APIs Supported | Status |
|-----|----------------|--------|
| Salesforce | REST API, Bulk API | ✅ Complete |
| HubSpot | CRM API, Forms API | ✅ Complete |
| Dynamics 365 | Web API | ✅ Complete |
| Generic REST | Custom APIs | ✅ Complete |
| Generic GraphQL | GraphQL APIs | ✅ Complete |

## 🎯 Use Cases

### 1. **Data Migration**
```python
# Migrate data from one CRM to another
source_connector = SalesforceConnector(source_config)
target_connector = HubSpotConnector(target_config)

# Transform and migrate all contacts
all_contacts = await source_connector.query('Contact', {})
await target_connector.bulk_create('contacts', transformed_contacts)
```

### 2. **Real-time Synchronization**
```python
# Set up continuous sync between CRMs
async def continuous_sync():
    while True:
        # Check for changes
        modified_records = await source_connector.query('Contact', {
            'LastModifiedDate': {'gte': last_sync_time}
        })
        
        # Sync changes
        if modified_records:
            await target_connector.synchronize(modified_records, 'contacts')
        
        last_sync_time = datetime.utcnow()
        await asyncio.sleep(60)  # Sync every minute
```

### 3. **Multi-CRM Dashboard**
```python
# Aggregate data from multiple CRMs
async def get_dashboard_data():
    connectors = {
        'salesforce': SalesforceConnector(sf_config),
        'hubspot': HubSpotConnector(hs_config),
        'dynamics': Dynamics365Connector(dyn_config)
    }
    
    # Fetch summary data from each CRM
    for name, connector in connectors.items():
        await connector.authenticate()
        contacts = await connector.query('contacts', {})
        print(f"{name}: {len(contacts)} contacts")
```

## 🛠️ Configuration

### Environment Variables

```bash
# Salesforce
export SF_CLIENT_ID=your_salesforce_client_id
export SF_CLIENT_SECRET=your_salesforce_client_secret
export SF_USERNAME=your_salesforce_username
export SF_PASSWORD=your_salesforce_password
export SF_SECURITY_TOKEN=your_salesforce_security_token
export SF_INSTANCE_URL=https://your-instance.salesforce.com

# HubSpot
export HS_CLIENT_ID=your_hubspot_client_id
export HS_CLIENT_SECRET=your_hubspot_client_secret
export HS_ACCESS_TOKEN=your_hubspot_access_token
export HS_PORTAL_ID=your_hubspot_portal_id

# Dynamics 365
export DYN_TENANT_ID=your_azure_tenant_id
export DYN_CLIENT_ID=your_azure_app_client_id
export DYN_CLIENT_SECRET=your_azure_app_client_secret
export DYN_RESOURCE_URL=https://yourorg.crm.dynamics.com
```

### Configuration File

```python
# config.py
import os
from dataclasses import dataclass

@dataclass
class CRMConfigs:
    salesforce = {
        'client_id': os.getenv('SF_CLIENT_ID'),
        'client_secret': os.getenv('SF_CLIENT_SECRET'),
        'username': os.getenv('SF_USERNAME'),
        'password': os.getenv('SF_PASSWORD'),
        'security_token': os.getenv('SF_SECURITY_TOKEN'),
        'instance_url': os.getenv('SF_INSTANCE_URL'),
        'rate_limit': {'max_calls': 100, 'time_window': 60}
    }
    
    hubspot = {
        'client_id': os.getenv('HS_CLIENT_ID'),
        'client_secret': os.getenv('HS_CLIENT_SECRET'),
        'access_token': os.getenv('HS_ACCESS_TOKEN'),
        'portal_id': os.getenv('HS_PORTAL_ID'),
        'rate_limit': {'max_calls': 100, 'time_window': 60}
    }
    
    dynamics = {
        'tenant_id': os.getenv('DYN_TENANT_ID'),
        'client_id': os.getenv('DYN_CLIENT_ID'),
        'client_secret': os.getenv('DYN_CLIENT_SECRET'),
        'resource_url': os.getenv('DYN_RESOURCE_URL')
    }
```

## 🔒 Security

- **OAuth 2.0**: Industry-standard authentication
- **Token Management**: Automatic token refresh
- **Rate Limiting**: Built-in API quota protection
- **Data Validation**: Input sanitization and validation
- **Secure Storage**: Environment variable support for credentials

## 📈 Performance

- **Async Operations**: Non-blocking I/O for high throughput
- **Batch Processing**: Efficient bulk operations
- **Connection Pooling**: Reuse connections for better performance
- **Rate Limiting**: Respect API limits automatically
- **Retry Logic**: Exponential backoff for resilience

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=crm_connectors tests/

# Run specific test
pytest tests/test_salesforce.py -v
```

## 📖 Documentation

- [Complete Documentation](docs/crm_integration.md)
- [API Reference](docs/crm_integration.md#api-reference)
- [Examples](code/enterprise_integration/crm_connectors/examples.py)

## 🤝 Examples

The `examples/` directory contains comprehensive examples:

- `salesforce_example()` - Basic Salesforce operations
- `hubspot_example()` - HubSpot integration with forms
- `dynamics_example()` - Dynamics 365 Web API usage
- `generic_rest_example()` - Custom REST API integration
- `generic_graphql_example()` - GraphQL API integration
- `cross_crm_synchronization_example()` - Multi-CRM sync

```bash
# Run examples (requires valid API credentials)
python -m crm_connectors.examples
```

## ⚡ Key Features in Detail

### Data Mapping
```python
# Configure field mappings
config = {
    'field_mappings': {
        'first_name': 'FirstName',      # Salesforce
        'last_name': 'LastName',
        'email': 'Email',
        # HubSpot mappings
        # 'first_name': 'firstname',
        # 'last_name': 'lastname',
        # 'email': 'email'
    }
}

# Or add mappings dynamically
connector.data_mapper.add_mapping('custom_field', 'ExternalField')
```

### Conflict Resolution
```python
# Timestamp-based (default)
sync_config = SyncConfig(
    conflict_resolution=ConflictResolution.TIMESTAMP
)

# Source wins
sync_config = SyncConfig(
    conflict_resolution=ConflictResolution.SOURCE_WINS
)

# Custom resolver
def my_resolver(source, target):
    return source.data.get('priority') > target.data.get('priority')

sync_config = SyncConfig(
    conflict_resolution=ConflictResolution.CUSTOM,
    custom_resolver=my_resolver
)
```

### Bulk Operations
```python
# Bulk create with automatic batching
large_dataset = [{'field': f'value_{i}'} for i in range(1000)]
results = await connector.bulk_create('contacts', large_dataset, batch_size=100)

# Monitor progress
for i, result in enumerate(results):
    if result.get('success'):
        print(f"Created record {i+1}/{len(results)}")
```

### Error Handling
```python
try:
    result = await connector.create('Contact', data)
except ValueError as e:
    # Invalid data
    print(f"Validation error: {e}")
except PermissionError as e:
    # Auth/permission error
    print(f"Access denied: {e}")
except ConnectionError as e:
    # Network/server error
    print(f"Connection error: {e}")
```

## 🐛 Troubleshooting

### Common Issues

**Authentication Failures**
```python
# Verify credentials and permissions
connector = SalesforceConnector(config)
result = await connector.test_connection()
print(result)
```

**Rate Limit Exceeded**
```python
# Configure rate limiting
config = {
    'rate_limit': {
        'max_calls': 50,      # Reduce calls
        'time_window': 60     # Shorter window
    }
}
```

**Field Mapping Errors**
```python
# Check available fields
fields = await connector.get_entity_schema('contacts')['fields']
print("Available fields:", fields)
```

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

- Documentation: [docs/crm_integration.md](docs/crm_integration.md)
- Issues: [GitHub Issues](https://github.com/your-org/crm-integrations/issues)
- Email: support@your-org.com

---

**Built with ❤️ for enterprise CRM integration**
