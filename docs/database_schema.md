# Database Schema Documentation

## Overview

This document describes the complete database schema for the Data Automation System built on Supabase/PostgreSQL. The schema implements a comprehensive data automation platform with role-based access control, audit logging, and scalable architecture.

## Schema Architecture

### Core Design Principles

1. **Security First**: All tables implement Row Level Security (RLS) policies
2. **Audit Trail**: Comprehensive audit logging for all sensitive operations
3. **Data Integrity**: Proper foreign key constraints and check constraints
4. **Performance**: Strategic indexing on frequently queried columns
5. **Scalability**: UUID primary keys and efficient data types
6. **Flexibility**: JSONB fields for metadata and dynamic configurations

## Database Tables

### 1. Users Table
**Purpose**: Manages user accounts and authentication
**Key Features**:
- Role-based access control (admin, manager, analyst, viewer)
- Soft delete support with `deleted_at` timestamp
- Two-factor authentication support
- Profile management with avatar support

```sql
Key Fields:
- id (UUID, Primary Key)
- email (VARCHAR, Unique)
- role (user_role ENUM)
- is_active (BOOLEAN)
- last_login (TIMESTAMPTZ)
```

**Access Control**:
- Users can view/edit their own profiles
- Admins can manage all users
- Public information includes email and name for collaborators

### 2. Documents Table
**Purpose**: Stores document metadata and file information
**Key Features**:
- Support for multiple document types (PDF, DOCX, XLSX, CSV, etc.)
- File integrity verification with checksums
- Metadata storage in JSONB format
- Tag-based organization
- Expiration handling with `expires_at`

```sql
Key Fields:
- id (UUID, Primary Key)
- filename (VARCHAR)
- file_path (TEXT)
- mime_type (VARCHAR)
- document_type (document_type ENUM)
- checksum (VARCHAR, Unique)
- metadata (JSONB)
- tags (TEXT[])
```

**Access Control**:
- Users can manage their own documents
- Analysts and above can view all documents
- Admins have full access

### 3. Document Processing Jobs Table
**Purpose**: Manages document processing workflow and status
**Key Features**:
- Queue-based job processing
- Progress tracking with percentage completion
- Retry mechanism with configurable limits
- Error handling and detailed error reporting
- Priority-based processing

```sql
Key Fields:
- id (UUID, Primary Key)
- document_id (UUID, Foreign Key)
- status (job_status ENUM)
- progress (INTEGER, 0-100)
- job_type (VARCHAR)
- retry_count (INTEGER)
- error_message (TEXT)
- processing_config (JSONB)
```

**Processing States**:
- `pending`: Job is queued for processing
- `processing`: Job is currently being processed
- `completed`: Job finished successfully
- `failed`: Job failed with errors
- `cancelled`: Job was cancelled before completion

### 4. Extracted Data Table
**Purpose**: Stores data extracted from processed documents
**Key Features**:
- Multiple data types (structured, semi-structured, unstructured)
- Confidence scoring for extraction quality
- Page and section references for positioning
- Method tracking for extraction techniques

```sql
Key Fields:
- id (UUID, Primary Key)
- job_id (UUID, Foreign Key)
- document_id (UUID, Foreign Key)
- data_type (data_type ENUM)
- extraction_method (VARCHAR)
- raw_data (JSONB)
- structured_data (JSONB)
- confidence_score (DECIMAL, 0-1)
```

### 5. Validation Results Table
**Purpose**: Tracks data validation and quality assessment
**Key Features**:
- Multiple validation status options
- Detailed error and warning reporting
- Rule-based validation configuration
- Validator identification

```sql
Key Fields:
- id (UUID, Primary Key)
- extracted_data_id (UUID, Foreign Key)
- validator_name (VARCHAR)
- validation_status (validation_status ENUM)
- validation_rules (JSONB)
- validation_errors (JSONB)
- validation_warnings (JSONB)
- validated_by (UUID, Foreign Key)
```

**Validation States**:
- `pending`: Validation not yet performed
- `valid`: Data passed all validation rules
- `invalid`: Data failed validation rules
- `warning`: Data has warnings but is acceptable
- `error`: Validation encountered system errors

### 6. Audit Logs Table
**Purpose**: Comprehensive audit trail for compliance and security
**Key Features**:
- IP address and user agent tracking
- Session-based logging
- Severity levels for filtering
- Before/after value tracking

```sql
Key Fields:
- id (UUID, Primary Key)
- user_id (UUID, Foreign Key)
- action (VARCHAR)
- resource_type (VARCHAR)
- resource_id (UUID)
- old_values (JSONB)
- new_values (JSONB)
- ip_address (INET)
- severity (VARCHAR)
```

**Severity Levels**:
- `debug`: Detailed debugging information
- `info`: General information events
- `warning`: Warning events
- `error`: Error events
- `critical`: Critical system events

### 7. Processing Metrics Table
**Purpose**: Performance monitoring and analytics
**Key Features**:
- Time-series metric storage
- Tagged metrics for filtering
- Job-specific performance tracking

```sql
Key Fields:
- id (UUID, Primary Key)
- job_id (UUID, Foreign Key)
- metric_type (VARCHAR)
- metric_name (VARCHAR)
- metric_value (NUMERIC)
- measurement_timestamp (TIMESTAMPTZ)
- tags (JSONB)
```

### 8. Integrations Table
**Purpose**: Manages external system integrations
**Key Features**:
- Support for multiple integration types
- Scheduled synchronization
- Encrypted credential storage
- Status tracking and error handling

```sql
Key Fields:
- id (UUID, Primary Key)
- name (VARCHAR)
- integration_type (integration_type ENUM)
- config (JSONB)
- credentials (JSONB, Encrypted)
- is_scheduled (BOOLEAN)
- schedule_cron (VARCHAR)
- last_sync_at (TIMESTAMPTZ)
- next_sync_at (TIMESTAMPTZ)
```

**Integration Types**:
- `api`: REST/SOAP API integrations
- `webhook`: Webhook-based integrations
- `database`: Database connections
- `file`: File-based integrations
- `email`: Email-based integrations
- `ftp`: FTP/SFTP integrations
- `s3`: AWS S3 integrations
- `other`: Custom integration types

### 9. Webhook Configs Table
**Purpose**: Manages webhook configurations and monitoring
**Key Features**:
- Multiple authentication methods
- Configurable retry logic
- Response monitoring
- Header and payload customization

```sql
Key Fields:
- id (UUID, Primary Key)
- integration_id (UUID, Foreign Key)
- target_url (TEXT)
- http_method (VARCHAR)
- headers (JSONB)
- payload_template (JSONB)
- authentication_type (VARCHAR)
- retry_config (JSONB)
- status (webhook_status ENUM)
```

### 10. System Settings Table
**Purpose**: Global system configuration management
**Key Features**:
- Public and private settings
- Encrypted value support
- Category-based organization
- Data type validation

```sql
Key Fields:
- id (UUID, Primary Key)
- key (VARCHAR, Unique)
- value (JSONB)
- category (VARCHAR)
- is_encrypted (BOOLEAN)
- is_public (BOOLEAN)
```

## Row Level Security (RLS) Policies

### Role Hierarchy
```
admin > manager > analyst > viewer
```

### Access Control Rules

#### Users Table
- **Self Access**: Users can view and edit their own profiles
- **Admin Access**: Admins can view, create, update, and delete all users
- **Public Fields**: Email and names may be visible to collaborators

#### Documents Table
- **Owner Access**: Users can manage their own documents
- **Analyst Access**: Analysts and above can view all documents
- **Admin Access**: Admins have full administrative access

#### Processing Jobs Table
- **Owner Related**: Users can view jobs for their documents
- **Analyst Access**: Analysts can view all processing jobs
- **System Access**: System processes can insert and update jobs

#### Extracted Data Table
- **Owner Related**: Users can view extracted data from their documents
- **Analyst Access**: Analysts can view all extracted data
- **System Access**: System processes manage data insertion

#### Validation Results Table
- **Owner Related**: Users can view validation results for their data
- **Analyst Access**: Analysts can view all validation results
- **Manager Access**: Managers can update validation results
- **System Access**: System processes insert validation results

#### Audit Logs Table
- **Self Access**: Users can view their own audit logs
- **Admin Access**: Admins can view all audit logs
- **System Access**: System processes insert audit logs

#### Integrations Table
- **Owner Access**: Users can manage their own integrations
- **Manager Access**: Managers can view all integrations
- **Admin Access**: Admins have full administrative access

#### Webhook Configs Table
- **Owner Related**: Users can manage webhooks for their integrations
- **Manager Access**: Managers can view all webhook configurations
- **Admin Access**: Admins have full administrative access

#### System Settings Table
- **Public Access**: All users can view public settings
- **Admin Access**: Admins can view and manage all settings

## Helper Functions

### get_user_role(user_id UUID)
Returns the current role of a user. Defaults to 'viewer' for inactive users.

### is_admin(user_id UUID)
Returns true if the user has admin role.

### has_role(user_id UUID, required_role user_role)
Returns true if the user has the required role or higher in the hierarchy.

### update_updated_at_column()
Trigger function to automatically update the `updated_at` timestamp.

### log_audit_event()
Trigger function to automatically log audit events for sensitive operations.

## Indexes and Performance

### Strategic Indexing
The schema includes carefully placed indexes to optimize common query patterns:

- **Primary Key Indexes**: All tables use UUID primary keys with default indexing
- **Foreign Key Indexes**: All foreign key relationships are indexed
- **Timestamp Indexes**: Temporal fields are indexed for time-series queries
- **JSONB Indexes**: JSONB fields use GIN indexes for efficient JSON queries
- **Array Indexes**: Array fields (like tags) use specialized indexes

### Performance Considerations

#### Document Processing
- Indexes on document type, upload timestamp, and uploader for efficient filtering
- GIN indexes on metadata and tags for flexible querying

#### Audit Logging
- Comprehensive indexing on user, action, resource type, and timestamp
- Separate indexes for severity levels and IP addresses

#### Integrations
- Indexes on integration type, active status, and sync scheduling
- JSONB indexes for configuration queries

## Views

### document_processing_overview
Aggregated view showing document processing status with job counts and timing information.

**Use Cases**:
- Dashboard metrics
- Processing queue management
- Performance monitoring

### integration_status_overview
Aggregated view showing integration status with webhook counts and error tracking.

**Use Cases**:
- Integration health monitoring
- System administration dashboard
- Error tracking and alerting

## Security Considerations

### Data Encryption
- Sensitive fields like credentials use JSONB storage with application-level encryption
- Password hashes are stored separately from other user data
- Two-factor authentication secrets are encrypted

### Access Control
- Row Level Security ensures users can only access authorized data
- Role hierarchy provides graduated access levels
- Public/private settings separation

### Audit Trail
- All sensitive operations are logged with full context
- IP address and user agent tracking for security analysis
- Before/after value tracking for change management

## Data Retention and Lifecycle

### Automatic Cleanup
- Documents can be automatically cleaned up based on `expires_at` timestamp
- Audit logs should have retention policies based on compliance requirements
- Processing metrics can be aggregated and old records purged

### Soft Deletes
- Users table supports soft deletes to preserve data integrity
- Other tables use cascading deletes for data consistency

## Initial Data

The schema includes essential default data:

### Default System Settings
- System version and configuration
- Processing limits and timeouts
- Security requirements
- Feature toggles
- Storage limits and allowed file types

### Default Admin User
- Email: `admin@system.local`
- Username: `admin`
- Password: `admin123` (must be changed immediately)
- Role: `admin`

## Migration and Deployment

### Database Extensions Required
- `uuid-ossp`: For UUID generation
- `pg_trgm`: For advanced text search capabilities
- `btree_gin`: For GIN index support

### Deployment Process
1. Create the migration in Supabase dashboard
2. Run the migration script
3. Verify all tables are created correctly
4. Test RLS policies with different user roles
5. Update the admin user password
6. Configure additional system settings as needed

## Maintenance and Monitoring

### Regular Tasks
- Monitor table sizes and index usage
- Review and rotate audit log data
- Update system settings as needed
- Monitor RLS policy performance

### Performance Monitoring
- Use the processing metrics table for performance tracking
- Monitor query performance on heavily indexed tables
- Review audit logs for security events

### Backup Strategy
- Regular automated backups of all tables
- Special attention to audit logs for compliance requirements
- Test restoration procedures regularly

## Compliance and Standards

### Data Privacy
- User data can be soft-deleted to meet privacy requirements
- Audit trails maintain compliance records
- Access logging for GDPR compliance

### Security Standards
- Row Level Security provides defense in depth
- Encrypted storage for sensitive credentials
- Comprehensive audit logging for security monitoring

### Scalability
- UUID primary keys support distributed systems
- JSONB fields allow schema evolution
- Proper indexing supports high-volume operations

## Future Enhancements

### Potential Improvements
- Partitioning for large tables (audit_logs, processing_metrics)
- Full-text search capabilities using external search engines
- Real-time subscriptions using Supabase Realtime
- GraphQL API layer for complex queries
- Data archival strategies for long-term storage

This schema provides a robust foundation for a data automation system with enterprise-grade security, scalability, and maintainability features.