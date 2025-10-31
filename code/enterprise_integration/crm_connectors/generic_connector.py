"""
Generic CRM Connector

Provides generic REST and GraphQL connectors for custom or unsupported CRM systems.

Features:
- OAuth 2.0 authentication
- REST API support with configurable endpoints
- GraphQL API support
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
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import logging

try:
    from .base import BaseCRMConnector, SyncRecord, SyncConfig, SyncResult
except ImportError:
    from base import BaseCRMConnector, SyncRecord, SyncConfig, SyncResult

logger = logging.getLogger(__name__)


class GenericConnector(BaseCRMConnector):
    """Generic connector for custom CRM APIs"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize generic connector
        
        Args:
            config: Configuration dictionary
                - base_url: Base URL for the API
                - auth_type: Authentication type (bearer, basic, api_key, oauth2)
                - auth_config: Authentication configuration
                - headers: Default headers for requests
                - timeout: Request timeout in seconds
        """
        super().__init__(config)
        self.base_url = config['base_url'].rstrip('/')
        self.auth_type = config.get('auth_type', 'bearer')
        self.auth_config = config.get('auth_config', {})
        self.default_headers = config.get('headers', {})
        self.timeout = config.get('timeout', 30)
        
        self.session = None
    
    async def authenticate(self) -> bool:
        """Authenticate with the generic API"""
        auth_type = self.auth_type.lower()
        
        if auth_type == 'bearer':
            return await self._authenticate_bearer()
        elif auth_type == 'basic':
            return await self._authenticate_basic()
        elif auth_type == 'api_key':
            return await self._authenticate_api_key()
        elif auth_type == 'oauth2':
            return await self._authenticate_oauth2()
        else:
            logger.warning(f"Unknown authentication type: {auth_type}")
            return True  # Assume no authentication needed
    
    async def _authenticate_bearer(self) -> bool:
        """Authenticate using Bearer token"""
        token = self.auth_config.get('token')
        if not token:
            raise ValueError("Bearer token is required")
        
        self.default_headers['Authorization'] = f'Bearer {token}'
        return True
    
    async def _authenticate_basic(self) -> bool:
        """Authenticate using Basic Auth"""
        username = self.auth_config.get('username')
        password = self.auth_config.get('password')
        
        if not username or not password:
            raise ValueError("Username and password are required for basic auth")
        
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.default_headers['Authorization'] = f'Basic {credentials}'
        return True
    
    async def _authenticate_api_key(self) -> bool:
        """Authenticate using API key"""
        api_key = self.auth_config.get('api_key')
        key_header = self.auth_config.get('key_header', 'X-API-Key')
        
        if not api_key:
            raise ValueError("API key is required")
        
        self.default_headers[key_header] = api_key
        return True
    
    async def _authenticate_oauth2(self) -> bool:
        """Authenticate using OAuth 2.0"""
        token_url = self.auth_config.get('token_url')
        client_id = self.auth_config.get('client_id')
        client_secret = self.auth_config.get('client_secret')
        grant_type = self.auth_config.get('grant_type', 'client_credentials')
        
        if not token_url or not client_id or not client_secret:
            raise ValueError("OAuth2 configuration is incomplete")
        
        data = {
            'grant_type': grant_type,
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        # Add additional parameters if provided
        if 'scope' in self.auth_config:
            data['scope'] = self.auth_config['scope']
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    access_token = result.get('access_token')
                    if access_token:
                        self.default_headers['Authorization'] = f'Bearer {access_token}'
                        return True
                else:
                    error_text = await response.text()
                    logger.error(f"OAuth2 authentication failed: {error_text}")
                    raise Exception(f"OAuth2 authentication failed: {error_text}")
        
        return False
    
    def _get_headers(self, additional_headers: Dict[str, str] = None) -> Dict[str, str]:
        """Get HTTP headers for API requests"""
        headers = self.default_headers.copy()
        
        if additional_headers:
            headers.update(additional_headers)
        
        # Ensure Content-Type and Accept are set
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
        if 'Accept' not in headers:
            headers['Accept'] = 'application/json'
        
        return headers
    
    async def _make_request(self, method: str, endpoint: str, 
                           data: Dict[str, Any] = None, 
                           params: Dict[str, Any] = None,
                           headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Make authenticated request to the API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self._get_headers(headers)
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(
                method, url, 
                headers=request_headers, 
                json=data, 
                params=params
            ) as response:
                if response.status >= 200 and response.status < 300:
                    if response.status == 204:
                        return {'success': True}
                    else:
                        content_type = response.headers.get('content-type', '')
                        if 'application/json' in content_type:
                            return await response.json()
                        else:
                            return {'data': await response.text()}
                else:
                    error_text = await response.text()
                    logger.error(f"API request failed: {response.status} - {error_text}")
                    raise Exception(f"API request failed: {response.status} - {error_text}")
    
    async def create(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record"""
        # Use custom endpoint if specified, otherwise use generic pattern
        endpoint = self.config.get('endpoints', {}).get('create', '').format(entity_type=entity_type)
        if not endpoint:
            endpoint = entity_type
        
        # Map data using data mapper
        external_data = self.data_mapper.map_to_external(data)
        
        return await self._execute_with_retry(
            self._make_request, 'POST', endpoint, data=external_data
        )
    
    async def read(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Read a single record"""
        # Use custom endpoint if specified, otherwise use generic pattern
        endpoint = self.config.get('endpoints', {}).get('read', '').format(entity_type=entity_type, id=entity_id)
        if not endpoint:
            endpoint = f"{entity_type}/{entity_id}"
        
        result = await self._execute_with_retry(
            self._make_request, 'GET', endpoint
        )
        
        # Map back to internal format
        return self.data_mapper.map_to_internal(result)
    
    async def update(self, entity_type: str, entity_id: str, 
                     data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing record"""
        # Use custom endpoint if specified, otherwise use generic pattern
        endpoint = self.config.get('endpoints', {}).get('update', '').format(entity_type=entity_type, id=entity_id)
        if not endpoint:
            endpoint = f"{entity_type}/{entity_id}"
        
        # Map data using data mapper
        external_data = self.data_mapper.map_to_external(data)
        
        return await self._execute_with_retry(
            self._make_request, 'PUT', endpoint, data=external_data
        )
    
    async def delete(self, entity_type: str, entity_id: str) -> bool:
        """Delete a record"""
        # Use custom endpoint if specified, otherwise use generic pattern
        endpoint = self.config.get('endpoints', {}).get('delete', '').format(entity_type=entity_type, id=entity_id)
        if not endpoint:
            endpoint = f"{entity_type}/{entity_id}"
        
        result = await self._execute_with_retry(
            self._make_request, 'DELETE', endpoint
        )
        return result.get('success', False)
    
    async def query(self, entity_type: str, filters: Dict[str, Any], 
                    fields: List[str] = None, limit: int = None) -> List[Dict[str, Any]]:
        """Query records"""
        # Use custom endpoint if specified, otherwise use generic pattern
        endpoint = self.config.get('endpoints', {}).get('query', '').format(entity_type=entity_type)
        if not endpoint:
            endpoint = entity_type
        
        params = {}
        
        # Add filters as query parameters
        if filters:
            for key, value in filters.items():
                params[key] = value
        
        # Add fields parameter
        if fields:
            params['fields'] = ','.join(fields)
        
        # Add limit parameter
        if limit:
            params['limit'] = limit
        
        result = await self._execute_with_retry(
            self._make_request, 'GET', endpoint, params=params
        )
        
        # Handle different response structures
        records = []
        if isinstance(result, dict):
            if 'data' in result:
                records = result['data']
            elif 'results' in result:
                records = result['results']
            elif 'items' in result:
                records = result['items']
            else:
                records = [result]  # Single record
        elif isinstance(result, list):
            records = result
        else:
            records = [result]
        
        # Map all records back to internal format
        mapped_records = [self.data_mapper.map_to_internal(record) 
                         for record in records]
        
        return mapped_records
    
    def get_supported_entities(self) -> List[str]:
        """Get list of supported entity types"""
        # Return configured entities or empty list for generic connector
        return self.config.get('supported_entities', [])
    
    def get_entity_schema(self, entity_type: str) -> Dict[str, Any]:
        """Get schema information for an entity type"""
        # Return configured schema or basic structure
        schemas = self.config.get('schemas', {})
        return schemas.get(entity_type, {
            'name': entity_type,
            'fields': [],
            'description': 'Generic entity'
        })
    
    async def synchronize(self, source_data: List[Dict[str, Any]], 
                         target_entity: str,
                         config: SyncConfig = None) -> SyncResult:
        """Synchronize data with the generic API"""
        if config is None:
            config = SyncConfig()
        
        start_time = datetime.utcnow()
        
        try:
            # Get target data from the API
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
        
        logger.info("Generic connector closed")


class RestConnector(GenericConnector):
    """Generic REST API connector"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize REST connector"""
        # Ensure REST-specific defaults
        config.setdefault('auth_type', 'bearer')
        super().__init__(config)


class GraphQLConnector(BaseCRMConnector):
    """Generic GraphQL API connector"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize GraphQL connector
        
        Args:
            config: Configuration dictionary
                - endpoint: GraphQL endpoint URL
                - auth_type: Authentication type
                - auth_config: Authentication configuration
        """
        super().__init__(config)
        self.graphql_endpoint = config['endpoint']
    
    async def authenticate(self) -> bool:
        """Authenticate with GraphQL endpoint"""
        # For GraphQL, authentication is typically handled in headers
        # Delegate to parent authenticate method
        await super().authenticate()
        return True
    
    async def execute_query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a GraphQL query"""
        request_data = {
            'query': query
        }
        
        if variables:
            request_data['variables'] = variables
        
        return await self._execute_with_retry(
            self._make_graphql_request, request_data
        )
    
    async def _make_graphql_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make GraphQL request"""
        url = self.graphql_endpoint
        headers = self._get_headers()
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=request_data) as response:
                if response.status >= 200 and response.status < 300:
                    result = await response.json()
                    
                    # Check for GraphQL errors
                    if 'errors' in result:
                        errors = result['errors']
                        logger.error(f"GraphQL errors: {errors}")
                        raise Exception(f"GraphQL errors: {errors}")
                    
                    return result.get('data', {})
                else:
                    error_text = await response.text()
                    logger.error(f"GraphQL request failed: {response.status} - {error_text}")
                    raise Exception(f"GraphQL request failed: {response.status} - {error_text}")
    
    async def create(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record using GraphQL mutation"""
        # Build GraphQL mutation
        field_list = ', '.join(data.keys())
        mutation = f"""
        mutation Create{entity_type.capitalize()}($data: {entity_type.capitalize()}Input!) {{
            create{entity_type.capitalize()}(data: $data) {{
                id
                {field_list}
            }}
        }}
        """
        
        variables = {'data': self.data_mapper.map_to_external(data)}
        
        result = await self.execute_query(mutation, variables)
        
        # Extract the created entity from result
        entity_key = f"create{entity_type.capitalize()}"
        if entity_key in result:
            return self.data_mapper.map_to_internal(result[entity_key])
        
        raise Exception(f"Unexpected GraphQL response structure: {result}")
    
    async def read(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Read a single record using GraphQL query"""
        # Build GraphQL query
        query = f"""
        query Get{entity_type.capitalize()}($id: ID!) {{
            {entity_type}(id: $id) {{
                id
            }}
        }}
        """
        
        variables = {'id': entity_id}
        
        result = await self.execute_query(query, variables)
        
        # Extract the entity from result
        if entity_type in result:
            return self.data_mapper.map_to_internal(result[entity_type])
        
        raise Exception(f"Entity not found: {entity_type}({entity_id})")
    
    async def update(self, entity_type: str, entity_id: str, 
                     data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing record using GraphQL mutation"""
        # Build GraphQL mutation
        field_list = ', '.join(data.keys())
        mutation = f"""
        mutation Update{entity_type.capitalize()}($id: ID!, $data: {entity_type.capitalize()}Input!) {{
            update{entity_type.capitalize()}(id: $id, data: $data) {{
                id
                {field_list}
            }}
        }}
        """
        
        variables = {
            'id': entity_id,
            'data': self.data_mapper.map_to_external(data)
        }
        
        result = await self.execute_query(mutation, variables)
        
        # Extract the updated entity from result
        entity_key = f"update{entity_type.capitalize()}"
        if entity_key in result:
            return self.data_mapper.map_to_internal(result[entity_key])
        
        raise Exception(f"Unexpected GraphQL response structure: {result}")
    
    async def delete(self, entity_type: str, entity_id: str) -> bool:
        """Delete a record using GraphQL mutation"""
        # Build GraphQL mutation
        mutation = f"""
        mutation Delete{entity_type.capitalize()}($id: ID!) {{
            delete{entity_type.capitalize()}(id: $id) {{
                success
            }}
        }}
        """
        
        variables = {'id': entity_id}
        
        result = await self.execute_query(mutation, variables)
        
        # Extract success status from result
        entity_key = f"delete{entity_type.capitalize()}"
        if entity_key in result:
            return result[entity_key].get('success', False)
        
        raise Exception(f"Unexpected GraphQL response structure: {result}")
    
    async def query(self, entity_type: str, filters: Dict[str, Any], 
                    fields: List[str] = None, limit: int = None) -> List[Dict[str, Any]]:
        """Query records using GraphQL query"""
        # Build field list for GraphQL query
        if not fields:
            fields = ['id']
        
        field_selection = '\n'.join([f"                {field}" for field in fields])
        
        # Build where clause for filters
        where_clause = ""
        if filters:
            filter_parts = []
            for key, value in filters.items():
                filter_parts.append(f"{key}: {self._format_graphql_value(value)}")
            where_clause = f"(where: {{ {' '.join(filter_parts)} }})"
        
        # Add limit
        limit_clause = f"(first: {limit})" if limit else ""
        
        query = f"""
        query Get{entity_type.capitalize()}s {where_clause} {limit_clause} {{
            {entity_type}s {where_clause} {limit_clause} {{
                id
{field_selection}
            }}
        }}
        """
        
        result = await self.execute_query(query)
        
        # Extract entities from result
        entities_key = f"{entity_type}s"
        if entities_key in result:
            records = result[entities_key]
            # Map all records back to internal format
            mapped_records = [self.data_mapper.map_to_internal(record) 
                            for record in records]
            return mapped_records
        
        return []
    
    def _format_graphql_value(self, value: Any) -> str:
        """Format value for GraphQL query"""
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            return f"[{', '.join([self._format_graphql_value(v) for v in value])}]"
        elif value is None:
            return "null"
        else:
            return f'"{str(value)}"'
    
    def get_supported_entities(self) -> List[str]:
        """Get list of supported entity types"""
        return self.config.get('supported_entities', [])
    
    def get_entity_schema(self, entity_type: str) -> Dict[str, Any]:
        """Get schema information for an entity type"""
        schemas = self.config.get('schemas', {})
        return schemas.get(entity_type, {
            'name': entity_type,
            'fields': [],
            'description': 'GraphQL entity'
        })
    
    async def close(self):
        """Close the connector and cleanup resources"""
        logger.info("GraphQL connector closed")
