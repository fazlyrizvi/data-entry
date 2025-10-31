"""
Microsoft Dynamics 365 CRM Connector

Supports Dynamics 365 Web API for interacting with Dynamics 365 CRM.

Features:
- OAuth 2.0 authentication with Azure AD
- Web API for standard operations
- Rate limiting
- Retry mechanisms with exponential backoff
- Data mapping and transformation
- Bidirectional synchronization
- Batch operations
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


class Dynamics365Connector(BaseCRMConnector):
    """Microsoft Dynamics 365 connector with Web API support"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Dynamics 365 connector
        
        Args:
            config: Configuration dictionary
                - tenant_id: Azure AD tenant ID
                - client_id: Azure AD application client ID
                - client_secret: Azure AD application client secret
                - resource_url: Dynamics 365 resource URL (organization URL)
                - api_version: API version (default: 9.2)
                - scope: OAuth scope (default: https://organization.crm.dynamics.com/.default)
                - rate_limit: Rate limiting configuration
        """
        super().__init__(config)
        self.tenant_id = config['tenant_id']
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.resource_url = config['resource_url']
        self.api_version = config.get('api_version', '9.2')
        self.scope = config.get('scope', f'{self.resource_url}/.default')
        
        self.access_token = None
        self.token_expiry = None
        self.session = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Dynamics 365 using OAuth 2.0"""
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': self.scope
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.access_token = result['access_token']
                    expires_in = result.get('expires_in', 3600)
                    self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    self.session = session
                    logger.info("Successfully authenticated with Dynamics 365")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Authentication failed: {error_text}")
                    raise Exception(f"Authentication failed: {error_text}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests"""
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json',
            'OData-MaxVersion': '4.0',
            'OData-Version': '4.0',
            'Prefer': 'odata.maxpagesize=500'
        }
        
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        return headers
    
    def _get_base_url(self) -> str:
        """Get base URL for Dynamics 365 Web API"""
        return f"{self.resource_url}/api/data/v{self.api_version}"
    
    def _build_odata_query(self, entity_type: str, filters: Dict[str, Any], 
                          fields: List[str] = None, expand: List[str] = None) -> str:
        """Build OData query string"""
        select_parts = []
        
        # Add select fields
        if fields:
            select_parts.extend(fields)
        else:
            select_parts.append('*')
        
        query = f"?$select={','.join(select_parts)}"
        
        # Add filters
        if filters:
            filter_clauses = []
            for field, value in filters.items():
                if isinstance(value, dict):
                    for op, val in value.items():
                        filter_clauses.append(self._build_filter_condition(field, op, val))
                else:
                    filter_clauses.append(self._build_filter_condition(field, 'eq', value))
            
            if filter_clauses:
                query += f"&$filter={' and '.join(filter_clauses)}"
        
        # Add expand for related entities
        if expand:
            expand_parts = []
            for related_entity in expand:
                expand_parts.append(f"$select=*&$expand={related_entity}($select=*)")
            query += f"&$expand={','.join(expand_parts)}"
        
        return query
    
    def _build_filter_condition(self, field: str, operator: str, value: Any) -> str:
        """Build a single filter condition"""
        if operator == 'eq':
            return f"{field} eq {self._format_odata_value(value)}"
        elif operator == 'ne':
            return f"{field} ne {self._format_odata_value(value)}"
        elif operator == 'gt':
            return f"{field} gt {self._format_odata_value(value)}"
        elif operator == 'gte':
            return f"{field} ge {self._format_odata_value(value)}"
        elif operator == 'lt':
            return f"{field} lt {self._format_odata_value(value)}"
        elif operator == 'lte':
            return f"{field} le {self._format_odata_value(value)}"
        elif operator == 'like':
            return f"contains({field}, {self._format_odata_value(value)})"
        elif operator == 'in':
            values = ','.join([self._format_odata_value(v) for v in value])
            return f"{field} in ({values})"
        else:
            raise ValueError(f"Unsupported operator: {operator}")
    
    def _format_odata_value(self, value: Any) -> str:
        """Format value for OData query"""
        if isinstance(value, str):
            # Escape single quotes
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (int, float)):
            return str(value)
        elif value is None:
            return 'null'
        else:
            # Default to string representation
            return f"'{str(value)}'"
    
    async def _make_request(self, method: str, url: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated request to Dynamics 365 Web API"""
        headers = self._get_headers()
        
        async with self.session.request(
            method, url, 
            headers=headers, 
            json=data
        ) as response:
            if method == 'DELETE' and response.status == 204:
                return {'success': True}
            
            if response.status >= 200 and response.status < 300:
                if response.status == 204:
                    return {'success': True}
                else:
                    result = await response.json()
                    return result
            else:
                error_text = await response.text()
                logger.error(f"API request failed: {response.status} - {error_text}")
                raise Exception(f"API request failed: {response.status} - {error_text}")
    
    async def create(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in Dynamics 365"""
        async def _create():
            url = f"{self._get_base_url()}/{entity_type}"
            
            # Map data using data mapper
            external_data = self.data_mapper.map_to_external(data)
            
            return await self._make_request('POST', url, data=external_data)
        
        result = await self._execute_with_retry(_create)
        
        # Extract GUID from the response (Dynamics 365 returns the created entity)
        return {
            'id': result.get(entity_type.replace('mscrm_', '') + 'id') or result.get('id'),
            'data': result
        }
    
    async def read(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Read a single record from Dynamics 365"""
        async def _read():
            url = f"{self._get_base_url()}/{entity_type}({entity_id})"
            
            return await self._make_request('GET', url)
        
        result = await self._execute_with_retry(_read)
        
        # Map back to internal format
        mapped_result = self.data_mapper.map_to_internal(result)
        return mapped_result
    
    async def update(self, entity_type: str, entity_id: str, 
                     data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing record in Dynamics 365"""
        async def _update():
            url = f"{self._get_base_url()}/{entity_type}({entity_id})"
            
            # Map data using data mapper
            external_data = self.data_mapper.map_to_external(data)
            
            return await self._make_request('PATCH', url, data=external_data)
        
        result = await self._execute_with_retry(_update)
        return {
            'id': entity_id,
            'success': True,
            'data': result
        }
    
    async def delete(self, entity_type: str, entity_id: str) -> bool:
        """Delete a record from Dynamics 365"""
        async def _delete():
            url = f"{self._get_base_url()}/{entity_type}({entity_id})"
            
            return await self._make_request('DELETE', url)
        
        result = await self._execute_with_retry(_delete)
        return result.get('success', False)
    
    async def query(self, entity_type: str, filters: Dict[str, Any], 
                    fields: List[str] = None, limit: int = None) -> List[Dict[str, Any]]:
        """Query records from Dynamics 365 using OData"""
        async def _query():
            # Build OData query
            query = self._build_odata_query(entity_type, filters, fields)
            url = f"{self._get_base_url()}/{entity_type}{query}"
            
            result = await self._make_request('GET', url)
            
            # Extract records from OData response
            records = result.get('value', [])
            
            # Map all records back to internal format
            mapped_records = [self.data_mapper.map_to_internal(record) 
                            for record in records]
            
            return mapped_records
        
        records = await self._execute_with_retry(_query)
        
        # Apply limit if specified (Dynamics 365 has its own paging mechanism)
        if limit and len(records) > limit:
            return records[:limit]
        
        return records
    
    async def execute_function(self, function_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a custom function in Dynamics 365"""
        async def _execute():
            url = f"{self._get_base_url()}/{function_name}"
            if params:
                # Add parameters to URL
                param_list = []
                for key, value in params.items():
                    param_list.append(f"{key}={self._format_odata_value(value)}")
                if param_list:
                    url += f"({','.join(param_list)})"
            else:
                url += "()"
            
            return await self._make_request('GET', url)
        
        return await self._execute_with_retry(_execute)
    
    async def associate_entities(self, entity_type: str, entity_id: str, 
                                related_entity_type: str, related_entity_id: str,
                                relationship_name: str) -> Dict[str, Any]:
        """Associate two entities in Dynamics 365"""
        async def _associate():
            url = f"{self._get_base_url()}/{entity_type}({entity_id})/{relationship_name}/$ref"
            
            data = {
                "@odata.context": f"{self._get_base_url()}/$metadata#{related_entity_type}/$ref",
                f"{related_entity_type}(@odata.id)": f"{self._get_base_url()}/{related_entity_type}({related_entity_id})"
            }
            
            return await self._make_request('POST', url, data=data)
        
        return await self._execute_with_retry(_associate)
    
    async def disassociate_entities(self, entity_type: str, entity_id: str,
                                   related_entity_type: str, related_entity_id: str,
                                   relationship_name: str) -> Dict[str, Any]:
        """Disassociate two entities in Dynamics 365"""
        async def _disassociate():
            url = f"{self._get_base_url()}/{entity_type}({entity_id})/{relationship_name}({related_entity_type}/{related_entity_id})/$ref"
            
            return await self._make_request('DELETE', url)
        
        return await self._execute_with_retry(_disassociate)
    
    async def bulk_create(self, entity_type: str, records: List[Dict[str, Any]], 
                          batch_size: int = 100) -> List[Dict[str, Any]]:
        """Create multiple records using batch operations"""
        results = []
        batch_size = min(batch_size, 1000)  # Dynamics 365 limit for batch operations
        
        # For large batches, we'll use individual requests with concurrency control
        semaphore = asyncio.Semaphore(10)  # Limit concurrent operations
        
        async def create_single_record(record):
            async with semaphore:
                try:
                    result = await self.create(entity_type, record)
                    return {'success': True, 'result': result}
                except Exception as e:
                    logger.error(f"Failed to create record: {str(e)}")
                    return {'success': False, 'error': str(e), 'record': record}
        
        # Create tasks for all records
        tasks = [create_single_record(record) for record in records]
        
        # Execute in batches
        for i in range(0, len(tasks), batch_size):
            batch_tasks = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append({'success': False, 'error': str(result)})
                else:
                    results.append(result)
            
            logger.info(f"Processed batch {i//batch_size + 1}, {len(batch_tasks)} records")
        
        return results
    
    async def bulk_update(self, entity_type: str, updates: List[Dict[str, Any]], 
                          batch_size: int = 100) -> List[Dict[str, Any]]:
        """Update multiple records using batch operations"""
        results = []
        batch_size = min(batch_size, 1000)  # Dynamics 365 limit for batch operations
        
        # For large batches, we'll use individual requests with concurrency control
        semaphore = asyncio.Semaphore(10)  # Limit concurrent operations
        
        async def update_single_record(update):
            async with semaphore:
                try:
                    entity_id = update.pop('id')
                    result = await self.update(entity_type, entity_id, update)
                    return {'success': True, 'result': result}
                except Exception as e:
                    logger.error(f"Failed to update record: {str(e)}")
                    return {'success': False, 'error': str(e), 'update': update}
        
        # Create tasks for all updates
        tasks = [update_single_record(update.copy()) for update in updates]
        
        # Execute in batches
        for i in range(0, len(tasks), batch_size):
            batch_tasks = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append({'success': False, 'error': str(result)})
                else:
                    results.append(result)
            
            logger.info(f"Processed batch {i//batch_size + 1}, {len(batch_tasks)} updates")
        
        return results
    
    async def who_am_i(self) -> Dict[str, Any]:
        """Get information about the current user and organization"""
        async def _who_am_i():
            url = f"{self._get_base_url()}/WhoAmI"
            
            return await self._make_request('GET', url)
        
        return await self._execute_with_retry(_who_am_i)
    
    async def get_entity_metadata(self, entity_type: str) -> Dict[str, Any]:
        """Get metadata for a specific entity"""
        async def _get_metadata():
            url = f"{self._get_base_url()}/EntityDefinitions(LogicalName='{entity_type}')"
            
            return await self._make_request('GET', url)
        
        return await self._execute_with_retry(_get_metadata)
    
    async def get_global_metadata(self) -> Dict[str, Any]:
        """Get global metadata for all entities"""
        async def _get_global_metadata():
            url = f"{self._get_base_url()}/EntityDefinitions"
            
            return await self._make_request('GET', url)
        
        result = await self._execute_with_retry(_get_global_metadata)
        return result.get('value', [])
    
    def get_supported_entities(self) -> List[str]:
        """Get list of supported entity types"""
        # Common Dynamics 365 entities
        return [
            'accounts', 'contacts', 'leads', 'opportunities', 'incidents',
            'tasks', 'appointments', 'campaigns', 'products', 'pricebooks',
            'orders', 'invoices', 'users', 'teams', 'businessunits'
        ]
    
    def get_entity_schema(self, entity_type: str) -> Dict[str, Any]:
        """Get schema information for an entity type"""
        # This would typically be populated by get_entity_metadata
        # For now, return a basic schema structure
        return {
            'name': entity_type,
            'attributes': [],
            'relationships': [],
            'keys': [],
            'queryable': True,
            'createable': True,
            'updateable': True,
            'deleteable': True
        }
    
    async def synchronize(self, source_data: List[Dict[str, Any]], 
                         target_entity: str,
                         config: SyncConfig = None) -> SyncResult:
        """Synchronize data with Dynamics 365"""
        if config is None:
            config = SyncConfig()
        
        start_time = datetime.utcnow()
        
        try:
            # Get target data from Dynamics 365
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
        
        logger.info("Dynamics 365 connector closed")
