"""
Salesforce CRM Connector

Supports both REST API and Bulk API for interacting with Salesforce CRM.

Features:
- OAuth 2.0 authentication
- REST API for standard operations
- Bulk API for large data operations
- Rate limiting
- Retry mechanisms with exponential backoff
- Data mapping and transformation
- Bidirectional synchronization
"""

import aiohttp
import asyncio
import json
import base64
import urllib.parse
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import logging

try:
    from .base import BaseCRMConnector, SyncRecord, SyncConfig, SyncResult
except ImportError:
    from base import BaseCRMConnector, SyncRecord, SyncConfig, SyncResult

logger = logging.getLogger(__name__)


class SalesforceConnector(BaseCRMConnector):
    """Salesforce CRM connector with REST and Bulk API support"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Salesforce connector
        
        Args:
            config: Configuration dictionary
                - client_id: Salesforce Connected App Client ID
                - client_secret: Salesforce Connected App Client Secret
                - username: Salesforce username
                - password: Salesforce password (with security token)
                - security_token: Salesforce security token
                - instance_url: Salesforce instance URL
                - api_version: API version (default: v58.0)
                - bulk_api_enabled: Enable Bulk API for large operations
                - rate_limit: Rate limiting configuration
        """
        super().__init__(config)
        self.api_version = config.get('api_version', 'v58.0')
        self.instance_url = config.get('instance_url')
        self.bulk_api_enabled = config.get('bulk_api_enabled', False)
        self.bulk_api_version = config.get('bulk_api_version', 'v58.0')
        
        self.session = None
        self.access_token = None
        self.refresh_token = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Salesforce using OAuth 2.0"""
        auth_method = self.config.get('auth_method', 'password')
        
        if auth_method == 'password':
            return await self._authenticate_password()
        elif auth_method == 'oauth':
            return await self._authenticate_oauth()
        else:
            raise ValueError(f"Unsupported authentication method: {auth_method}")
    
    async def _authenticate_password(self) -> bool:
        """Authenticate using username/password flow"""
        if not self.instance_url:
            raise ValueError("Instance URL is required for password authentication")
        
        auth_url = f"{self.instance_url}/services/oauth2/token"
        
        # Prepare credentials
        username = self.config['username']
        password = self.config['password']
        security_token = self.config.get('security_token', '')
        
        # The password should include security token appended
        full_password = f"{password}{security_token}"
        client_id = self.config['client_id']
        client_secret = self.config['client_secret']
        
        data = {
            'grant_type': 'password',
            'client_id': client_id,
            'client_secret': client_secret,
            'username': username,
            'password': full_password
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(auth_url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.access_token = result['access_token']
                    self.refresh_token = result.get('refresh_token')
                    
                    # Update instance URL if different
                    if 'instance_url' in result:
                        self.instance_url = result['instance_url']
                    
                    self.session = session
                    logger.info("Successfully authenticated with Salesforce")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Authentication failed: {error_text}")
                    raise Exception(f"Authentication failed: {error_text}")
    
    async def _authenticate_oauth(self) -> bool:
        """Authenticate using OAuth 2.0 authorization code flow"""
        # This would typically redirect user for authorization
        # For server-to-server integration, password flow is preferred
        raise NotImplementedError("OAuth authorization code flow not implemented. Use password flow.")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        return headers
    
    def _build_soql_query(self, entity_type: str, filters: Dict[str, Any], 
                         fields: List[str] = None, limit: int = None) -> str:
        """Build SOQL query from filters"""
        # Default fields if none specified
        if not fields:
            fields = ['Id']
        
        # Start with SELECT clause
        query = f"SELECT {', '.join(fields)} FROM {entity_type}"
        
        # Add WHERE clause for filters
        if filters:
            where_clauses = []
            for field, value in filters.items():
                if isinstance(value, dict):
                    for op, val in value.items():
                        if op == 'eq':
                            where_clauses.append(f"{field} = '{val}'")
                        elif op == 'ne':
                            where_clauses.append(f"{field} != '{val}'")
                        elif op == 'gt':
                            where_clauses.append(f"{field} > '{val}'")
                        elif op == 'gte':
                            where_clauses.append(f"{field} >= '{val}'")
                        elif op == 'lt':
                            where_clauses.append(f"{field} < '{val}'")
                        elif op == 'lte':
                            where_clauses.append(f"{field} <= '{val}'")
                        elif op == 'like':
                            where_clauses.append(f"{field} LIKE '%{val}%'")
                        elif op == 'in':
                            values = ','.join([f"'{v}'" for v in val])
                            where_clauses.append(f"{field} IN ({values})")
                else:
                    where_clauses.append(f"{field} = '{value}'")
            
            if where_clauses:
                query += f" WHERE {' AND '.join(where_clauses)}"
        
        # Add LIMIT clause
        if limit:
            query += f" LIMIT {limit}"
        
        return query
    
    async def create(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in Salesforce"""
        async def _create():
            url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/{entity_type}/"
            
            # Map data using data mapper
            external_data = self.data_mapper.map_to_external(data)
            
            async with self.session.post(url, 
                                       headers=self._get_headers(),
                                       json=external_data) as response:
                if response.status == 201:
                    result = await response.json()
                    return {
                        'id': result['id'],
                        'success': True,
                        'errors': []
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Create failed: {error_text}")
                    raise Exception(f"Create failed: {error_text}")
        
        return await self._execute_with_retry(_create)
    
    async def read(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Read a single record from Salesforce"""
        async def _read():
            url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/{entity_type}/{entity_id}"
            
            async with self.session.get(url, headers=self._get_headers()) as response:
                if response.status == 200:
                    result = await response.json()
                    # Map back to internal format
                    return self.data_mapper.map_to_internal(result)
                else:
                    error_text = await response.text()
                    logger.error(f"Read failed: {error_text}")
                    raise Exception(f"Read failed: {error_text}")
        
        return await self._execute_with_retry(_read)
    
    async def update(self, entity_type: str, entity_id: str, 
                     data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing record in Salesforce"""
        async def _update():
            url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/{entity_type}/{entity_id}"
            
            # Map data using data mapper
            external_data = self.data_mapper.map_to_external(data)
            
            async with self.session.patch(url, 
                                        headers=self._get_headers(),
                                        json=external_data) as response:
                if response.status == 204:
                    return {
                        'id': entity_id,
                        'success': True,
                        'errors': []
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Update failed: {error_text}")
                    raise Exception(f"Update failed: {error_text}")
        
        return await self._execute_with_retry(_update)
    
    async def delete(self, entity_type: str, entity_id: str) -> bool:
        """Delete a record from Salesforce"""
        async def _delete():
            url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/{entity_type}/{entity_id}"
            
            async with self.session.delete(url, headers=self._get_headers()) as response:
                if response.status == 204:
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Delete failed: {error_text}")
                    raise Exception(f"Delete failed: {error_text}")
        
        return await self._execute_with_retry(_delete)
    
    async def query(self, entity_type: str, filters: Dict[str, Any], 
                    fields: List[str] = None, limit: int = None) -> List[Dict[str, Any]]:
        """Query records from Salesforce using SOQL"""
        async def _query():
            # Build SOQL query
            soql = self._build_soql_query(entity_type, filters, fields, limit)
            
            # URL encode the query
            encoded_query = urllib.parse.quote(soql)
            url = f"{self.instance_url}/services/data/{self.api_version}/query/?q={encoded_query}"
            
            async with self.session.get(url, headers=self._get_headers()) as response:
                if response.status == 200:
                    result = await response.json()
                    records = result.get('records', [])
                    
                    # Map all records back to internal format
                    mapped_records = [self.data_mapper.map_to_internal(record) 
                                    for record in records]
                    
                    return mapped_records
                else:
                    error_text = await response.text()
                    logger.error(f"Query failed: {error_text}")
                    raise Exception(f"Query failed: {error_text}")
        
        return await self._execute_with_retry(_query)
    
    async def bulk_create(self, entity_type: str, records: List[Dict[str, Any]], 
                          batch_size: int = 100) -> List[Dict[str, Any]]:
        """Create records using Bulk API for large datasets"""
        if not self.bulk_api_enabled:
            # Fallback to REST API for small batches
            return await super().bulk_create(entity_type, records, batch_size)
        
        return await self._bulk_api_operation('insert', entity_type, records)
    
    async def bulk_update(self, entity_type: str, updates: List[Dict[str, Any]], 
                          batch_size: int = 100) -> List[Dict[str, Any]]:
        """Update records using Bulk API for large datasets"""
        if not self.bulk_api_enabled:
            # Fallback to REST API for small batches
            return await super().bulk_update(entity_type, updates, batch_size)
        
        return await self._bulk_api_operation('update', entity_type, updates)
    
    async def bulk_delete(self, entity_type: str, entity_ids: List[str], 
                          batch_size: int = 100) -> List[Dict[str, Any]]:
        """Delete records using Bulk API for large datasets"""
        if not self.bulk_api_enabled:
            # Fallback to REST API for small batches
            results = []
            for entity_id in entity_ids:
                try:
                    result = await self.delete(entity_type, entity_id)
                    results.append({'id': entity_id, 'success': result})
                except Exception as e:
                    results.append({'id': entity_id, 'success': False, 'error': str(e)})
            return results
        
        records = [{'Id': entity_id} for entity_id in entity_ids]
        return await self._bulk_api_operation('delete', entity_type, records)
    
    async def _bulk_api_operation(self, operation: str, entity_type: str, 
                                  records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute Bulk API operation"""
        # This is a simplified Bulk API implementation
        # Full implementation would include job creation, batch processing, etc.
        
        logger.info(f"Starting Bulk API {operation} operation for {len(records)} records")
        
        # For demonstration, we'll use REST API with smaller batches
        # In production, implement full Bulk API workflow:
        # 1. Create job
        # 2. Create batches
        # 3. Close job
        # 4. Check results
        
        results = []
        batch_size = min(100, len(records))
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            if operation == 'insert':
                for record in batch:
                    try:
                        result = await self.create(entity_type, record)
                        results.append(result)
                    except Exception as e:
                        results.append({'success': False, 'error': str(e), 'record': record})
            elif operation == 'update':
                for record in batch:
                    try:
                        entity_id = record.pop('Id')
                        result = await self.update(entity_type, entity_id, record)
                        results.append(result)
                    except Exception as e:
                        results.append({'success': False, 'error': str(e), 'record': record})
            elif operation == 'delete':
                for record in batch:
                    try:
                        entity_id = record['Id']
                        result = await self.delete(entity_type, entity_id)
                        results.append({'id': entity_id, 'success': result})
                    except Exception as e:
                        results.append({'id': record.get('Id'), 'success': False, 'error': str(e)})
        
        logger.info(f"Bulk API operation completed. {len(results)} records processed")
        return results
    
    async def describe_object(self, entity_type: str) -> Dict[str, Any]:
        """Get object metadata from Salesforce"""
        async def _describe():
            url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/{entity_type}/describe/"
            
            async with self.session.get(url, headers=self._get_headers()) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Describe failed: {error_text}")
                    raise Exception(f"Describe failed: {error_text}")
        
        return await self._execute_with_retry(_describe)
    
    async def get_global_describe(self) -> Dict[str, Any]:
        """Get global describe of all available objects"""
        async def _global_describe():
            url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/"
            
            async with self.session.get(url, headers=self._get_headers()) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Global describe failed: {error_text}")
                    raise Exception(f"Global describe failed: {error_text}")
        
        return await self._execute_with_retry(_global_describe)
    
    def get_supported_entities(self) -> List[str]:
        """Get list of supported entity types"""
        # Common Salesforce objects
        return [
            'Account', 'Contact', 'Lead', 'Opportunity', 'Case', 'Task',
            'Event', 'Campaign', 'Product', 'Pricebook2', 'Quote',
            'Contract', 'Order', 'Asset', 'User', 'Profile'
        ]
    
    def get_entity_schema(self, entity_type: str) -> Dict[str, Any]:
        """Get schema information for an entity type"""
        # This would typically be populated by describe_object
        # For now, return a basic schema structure
        return {
            'name': entity_type,
            'fields': [],
            'relationships': [],
            'queryable': True,
            'createable': True,
            'updateable': True,
            'deleteable': True
        }
    
    async def synchronize(self, source_data: List[Dict[str, Any]], 
                         target_entity: str,
                         config: SyncConfig = None) -> SyncResult:
        """Synchronize data with Salesforce"""
        if config is None:
            config = SyncConfig()
        
        start_time = datetime.utcnow()
        
        try:
            # Get target data from Salesforce
            target_data = await self.query(target_entity, {})
            
            # Convert to sync records
            source_records = self.create_sync_records(source_data)
            target_records = self.create_sync_records(target_data)
            
            # Perform synchronization
            result = self._sync_records(source_records, target_records, config)
            
            # Process the synchronization results
            if config.direction in [SyncDirection.PUSH, SyncDirection.BIDIRECTIONAL]:
                for record in source_records:
                    if record.id not in [r.id for r in target_records]:
                        # Create new records
                        try:
                            await self.create(target_entity, record.data)
                            result.records_succeeded += 1
                        except Exception as e:
                            result.records_failed += 1
                            result.errors.append(f"Create failed for {record.id}: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Synchronization failed: {str(e)}")
            return SyncResult(
                success=False,
                errors=[str(e)],
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def close(self):
        """Close the connector and cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("Salesforce connector closed")
