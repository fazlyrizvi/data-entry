"""
CRM API Connectors - Enterprise Integration Module

This package provides secure API connectors for major CRM systems including:
- Salesforce (REST API, Bulk API)
- HubSpot (CRM API, Forms API)
- Microsoft Dynamics 365 (Web API)
- Generic REST/GraphQL connectors

Features:
- OAuth 2.0 authentication
- Rate limiting
- Retry mechanisms with exponential backoff
- Data mapping capabilities
- Bidirectional data synchronization
- Conflict resolution
- Bulk operations for large datasets
"""

from .base import BaseCRMConnector, SyncDirection, ConflictResolution
from .salesforce_connector import SalesforceConnector
from .hubspot_connector import HubSpotConnector
from .dynamics_connector import Dynamics365Connector
from .generic_connector import GenericConnector, RestConnector, GraphQLConnector

__all__ = [
    'BaseCRMConnector',
    'SyncDirection',
    'ConflictResolution',
    'SalesforceConnector',
    'HubSpotConnector',
    'Dynamics365Connector',
    'GenericConnector',
    'RestConnector',
    'GraphQLConnector'
]

__version__ = '1.0.0'
