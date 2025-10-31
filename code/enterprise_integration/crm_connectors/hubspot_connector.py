"""
HubSpot CRM Connector

Supports HubSpot CRM API and Forms API for interacting with HubSpot CRM.

Features:
- OAuth 2.0 authentication
- CRM API for standard operations
- Forms API for form submissions
- Rate limiting
- Retry mechanisms with exponential backoff
- Data mapping and transformation
- Bidirectional synchronization
"""

import aiohttp
import asyncio
import json
import base64
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import logging

try:
    from .base import BaseCRMConnector, SyncRecord, SyncConfig, SyncResult
except ImportError:
    from base import BaseCRMConnector, SyncRecord, SyncConfig, SyncResult

logger = logging.getLogger(__name__)


class HubSpotConnector(BaseCRMConnector):
    """HubSpot CRM connector with CRM API and Forms API support"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize HubSpot connector
        
        Args:
            config: Configuration dictionary
                - client_id: HubSpot App Client ID
                - client_secret: HubSpot App Client Secret
                - access_token: HubSpot access token
                - refresh_token: HubSpot refresh token
                - portal_id: HubSpot portal ID
                - api_url: HubSpot API URL (default: https://api.hubapi.com)
                - rate_limit: Rate limiting configuration
        """
        super().__init__(config)
        self.api_url = config.get('api_url', 'https://api.hubapi.com')
        self.portal_id = config.get('portal_id')
        self.access_token = config.get('access_token')
        self.refresh_token = config.get('refresh_token')
        
        self.session = None
        self._rate_limit_remaining = None
        self._rate_limit_reset = None
    
    async def authenticate(self) -> bool:
        """Authenticate with HubSpot using OAuth 2.0"""
        if self.access_token:
            # Verify token by making a test request
            try:
                await self._make_request('GET', '/account-info/v3/api-usage/daily')
                return True
            except Exception as e:
                logger.warning(f"Access token verification failed: {str(e)}")
                if self.refresh_token:
                    return await self._refresh_access_token()
                raise
        
        if self.refresh_token:
            return await self._refresh_access_token()
        
        raise ValueError("No access token or refresh token provided")
    
    async def _refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token"""
        auth_url = 'https://api.hubapi.com/oauth/v1/token'
        
        data = {
            'grant_type': 'refresh_token',
            'client_id': self.config['client_id'],
            'client_secret': self.config['client_secret'],
            'refresh_token': self.refresh_token
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(auth_url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.access_token = result['access_token']
                    self.refresh_token = result.get('refresh_token', self.refresh_token)
                    logger.info("Successfully refreshed HubSpot access token")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Token refresh failed: {error_text}")
                    raise Exception(f"Token refresh failed: {error_text}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        return headers
    
    async def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None,
                           params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated request to HubSpot API"""
        url = f"{self.api_url}{endpoint}"
        headers = self._get_headers()
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method, url, 
                headers=headers, 
                json=data, 
                params=params
            ) as response:
                # Update rate limit information
                if 'X-RateLimit-Remaining' in response.headers:
                    self._rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
                if 'X-RateLimit-Reset' in response.headers:
                    self._rate_limit_reset = int(response.headers['X-RateLimit-Reset'])
                
                if response.status == 429:  # Rate limit exceeded
                    reset_time = self._rate_limit_reset or int(datetime.utcnow().timestamp()) + 60
                    sleep_time = reset_time - int(datetime.utcnow().timestamp())
                    if sleep_time > 0:
                        logger.warning(f"Rate limit exceeded. Sleeping for {sleep_time} seconds")
                        await asyncio.sleep(sleep_time)
                        return await self._make_request(method, endpoint, data, params)
                
                if response.status >= 200 and response.status < 300:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"API request failed: {response.status} - {error_text}")
                    raise Exception(f"API request failed: {response.status} - {error_text}")
    
    async def create(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in HubSpot"""
        # Map data using data mapper
        external_data = self.data_mapper.map_to_external(data)
        
        # HubSpot uses specific endpoint structure for different object types
        if entity_type in ['contacts', 'companies', 'deals', 'tickets']:
            endpoint = f"/crm/v3/objects/{entity_type}"
        else:
            endpoint = f"/crm/v3/objects/{entity_type}"
        
        result = await self._make_request('POST', endpoint, data=external_data)
        
        return {
            'id': result.get('id'),
            'properties': result.get('properties', {}),
            'createdAt': result.get('createdAt'),
            'updatedAt': result.get('updatedAt'),
            'archived': result.get('archived', False)
        }
    
    async def read(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Read a single record from HubSpot"""
        # HubSpot uses specific endpoint structure for different object types
        if entity_type in ['contacts', 'companies', 'deals', 'tickets']:
            endpoint = f"/crm/v3/objects/{entity_type}/{entity_id}"
        else:
            endpoint = f"/crm/v3/objects/{entity_type}/{entity_id}"
        
        result = await self._make_request('GET', endpoint)
        
        # Map back to internal format
        mapped_result = self.data_mapper.map_to_internal(result)
        return mapped_result
    
    async def update(self, entity_type: str, entity_id: str, 
                     data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing record in HubSpot"""
        # Map data using data mapper
        external_data = self.data_mapper.map_to_external(data)
        
        # HubSpot uses specific endpoint structure for different object types
        if entity_type in ['contacts', 'companies', 'deals', 'tickets']:
            endpoint = f"/crm/v3/objects/{entity_type}/{entity_id}"
        else:
            endpoint = f"/crm/v3/objects/{entity_type}/{entity_id}"
        
        result = await self._make_request('PATCH', endpoint, data=external_data)
        
        return {
            'id': result.get('id'),
            'properties': result.get('properties', {}),
            'createdAt': result.get('createdAt'),
            'updatedAt': result.get('updatedAt'),
            'archived': result.get('archived', False)
        }
    
    async def delete(self, entity_type: str, entity_id: str) -> bool:
        """Delete a record from HubSpot"""
        # HubSpot uses specific endpoint structure for different object types
        if entity_type in ['contacts', 'companies', 'deals', 'tickets']:
            endpoint = f"/crm/v3/objects/{entity_type}/{entity_id}"
        else:
            endpoint = f"/crm/v3/objects/{entity_type}/{entity_id}"
        
        await self._make_request('DELETE', endpoint)
        return True
    
    async def query(self, entity_type: str, filters: Dict[str, Any], 
                    fields: List[str] = None, limit: int = None) -> List[Dict[str, Any]]:
        """Query records from HubSpot using the Search API"""
        # Build search request
        search_request = {
            'filterGroups': [],
            'sorts': [],
            'properties': fields or ['id'],
            'limit': min(limit or 100, 10000),  # HubSpot max limit is 10000
            'after': 0
        }
        
        # Add filters
        if filters:
            filter_group = {'filters': []}
            for field, value in filters.items():
                if isinstance(value, dict):
                    for op, val in value.items():
                        hubspot_operator = self._map_filter_operator(op)
                        filter_group['filters'].append({
                            'propertyName': field,
                            'operator': hubspot_operator,
                            'value': str(val)
                        })
                else:
                    filter_group['filters'].append({
                        'propertyName': field,
                        'operator': 'EQ',
                        'value': str(value)
                    })
            search_request['filterGroups'].append(filter_group)
        
        # HubSpot uses specific endpoint structure for different object types
        if entity_type in ['contacts', 'companies', 'deals', 'tickets']:
            endpoint = f"/crm/v3/objects/{entity_type}/search"
        else:
            endpoint = f"/crm/v3/objects/{entity_type}/search"
        
        results = []
        
        while True:
            response = await self._make_request('POST', endpoint, data=search_request)
            
            records = response.get('results', [])
            for record in records:
                # Map each record back to internal format
                mapped_record = self.data_mapper.map_to_internal(record)
                results.append(mapped_record)
            
            # Check if there are more results
            if not response.get('paging', {}).get('next'):
                break
            
            # Update after parameter for next page
            after_token = response['paging']['next']['after']
            search_request['after'] = after_token
        
        return results
    
    def _map_filter_operator(self, operator: str) -> str:
        """Map internal operator to HubSpot operator"""
        operator_map = {
            'eq': 'EQ',
            'ne': 'NEQ',
            'gt': 'GT',
            'gte': 'GTE',
            'lt': 'LT',
            'lte': 'LTE',
            'like': 'CONTAINS_TOKEN',
            'in': 'IN'
        }
        return operator_map.get(operator.lower(), 'EQ')
    
    async def bulk_create(self, entity_type: str, records: List[Dict[str, Any]], 
                          batch_size: int = 100) -> List[Dict[str, Any]]:
        """Create multiple records using batch API"""
        results = []
        batch_size = min(batch_size, 100)  # HubSpot batch limit
        
        # HubSpot batch endpoint
        if entity_type in ['contacts', 'companies', 'deals', 'tickets']:
            endpoint = f"/crm/v3/objects/{entity_type}/batch/create"
        else:
            endpoint = f"/crm/v3/objects/{entity_type}/batch/create"
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            # Map all records
            mapped_batch = [
                {'properties': self.data_mapper.map_to_external(record)}
                for record in batch
            ]
            
            try:
                response = await self._make_request('POST', endpoint, data={'inputs': mapped_batch})
                batch_results = response.get('results', [])
                results.extend(batch_results)
            except Exception as e:
                logger.error(f"Batch create failed: {str(e)}")
                # Add error entries for each record in batch
                for j, record in enumerate(batch):
                    results.append({
                        'success': False,
                        'error': str(e),
                        'record': record,
                        'index': i + j
                    })
        
        return results
    
    async def bulk_update(self, entity_type: str, updates: List[Dict[str, Any]], 
                          batch_size: int = 100) -> List[Dict[str, Any]]:
        """Update multiple records using batch API"""
        results = []
        batch_size = min(batch_size, 100)  # HubSpot batch limit
        
        # HubSpot batch endpoint
        if entity_type in ['contacts', 'companies', 'deals', 'tickets']:
            endpoint = f"/crm/v3/objects/{entity_type}/batch/update"
        else:
            endpoint = f"/crm/v3/objects/{entity_type}/batch/update"
        
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            
            # Map all records
            mapped_batch = []
            for update in batch:
                entity_id = update.pop('id', update.pop('hs_object_id', None))
                if entity_id:
                    mapped_batch.append({
                        'id': entity_id,
                        'properties': self.data_mapper.map_to_external(update)
                    })
            
            if not mapped_batch:
                continue
            
            try:
                response = await self._make_request('POST', endpoint, data={'inputs': mapped_batch})
                batch_results = response.get('results', [])
                results.extend(batch_results)
            except Exception as e:
                logger.error(f"Batch update failed: {str(e)}")
                # Add error entries for each record in batch
                for j, update in enumerate(batch):
                    results.append({
                        'success': False,
                        'error': str(e),
                        'update': update,
                        'index': i + j
                    })
        
        return results
    
    async def submit_form(self, form_id: str, data: Dict[str, Any], 
                         portal_id: str = None) -> Dict[str, Any]:
        """Submit data to a HubSpot form"""
        portal_id = portal_id or self.portal_id
        if not portal_id:
            raise ValueError("Portal ID is required for form submission")
        
        endpoint = f"/form-integrations/v1/integration/submit/{portal_id}/{form_id}"
        
        # Format form data
        form_data = {
            'fields': [
                {'name': field, 'value': value}
                for field, value in data.items()
            ],
            'context': {
                'pageUri': self.config.get('page_uri', ''),
                'pageName': self.config.get('page_name', '')
            }
        }
        
        result = await self._make_request('POST', endpoint, data=form_data)
        return result
    
    async def get_forms(self, portal_id: str = None) -> List[Dict[str, Any]]:
        """Get all forms from HubSpot"""
        portal_id = portal_id or self.portal_id
        if not portal_id:
            raise ValueError("Portal ID is required")
        
        endpoint = f"/form-integrations/v1/forms/{portal_id}"
        
        result = await self._make_request('GET', endpoint)
        return result.get('forms', [])
    
    async def get_object_properties(self, object_type: str) -> List[Dict[str, Any]]:
        """Get properties for a specific object type"""
        endpoint = f"/crm/v3/properties/{object_type}"
        
        result = await self._make_request('GET', endpoint)
        return result.get('results', [])
    
    async def get_rate_limits(self) -> Dict[str, Any]:
        """Get current rate limit information"""
        endpoint = '/account-info/v3/api-usage/daily'
        
        result = await self._make_request('GET', endpoint)
        return result
    
    def get_supported_entities(self) -> List[str]:
        """Get list of supported entity types"""
        return [
            'contacts', 'companies', 'deals', 'tickets',
            'products', 'line_items', 'quotes', 'owners',
            'lists', 'workflows', 'engagements', 'tasks'
        ]
    
    def get_entity_schema(self, entity_type: str) -> Dict[str, Any]:
        """Get schema information for an entity type"""
        # This would typically be populated by get_object_properties
        # For now, return a basic schema structure
        return {
            'name': entity_type,
            'properties': [],
            'associations': [],
            'searchable': True,
            'createable': True,
            'updateable': True,
            'deleteable': True
        }
    
    async def synchronize(self, source_data: List[Dict[str, Any]], 
                         target_entity: str,
                         config: SyncConfig = None) -> SyncResult:
        """Synchronize data with HubSpot"""
        if config is None:
            config = SyncConfig()
        
        start_time = datetime.utcnow()
        
        try:
            # Get target data from HubSpot
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
        
        logger.info("HubSpot connector closed")
