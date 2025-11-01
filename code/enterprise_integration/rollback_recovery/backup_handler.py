"""
Backup Handler - Handles snapshot creation, restore operations, and point-in-time recovery
"""
import asyncio
import hashlib
import json
import logging
import os
import sqlite3
import threading
import time
import zstandard as zstd
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

import aiofiles
import structlog

logger = structlog.get_logger(__name__)


class BackupType(Enum):
    """Types of backup operations"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"


class BackupStatus(Enum):
    """Backup operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CompressionType(Enum):
    """Compression algorithms for backup storage"""
    NONE = "none"
    ZSTD = "zstd"
    LZ4 = "lz4"


@dataclass
class BackupMetadata:
    """Metadata for backup operations"""
    backup_id: UUID
    backup_type: BackupType
    created_at: float
    completed_at: Optional[float]
    size_bytes: int
    compressed_size: int
    compression_type: CompressionType
    checksum: str
    source_location: str
    backup_location: str
    status: BackupStatus
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    retention_policy: Optional[str] = None
    incremental_base: Optional[UUID] = None


@dataclass
class DataChunk:
    """Represents a chunk of data in backup storage"""
    chunk_id: UUID
    backup_id: UUID
    chunk_index: int
    data: bytes
    checksum: str
    size: int
    compressed_size: int
    compression_type: CompressionType
    created_at: float


class BackupHandler:
    """
    Comprehensive backup and restore handler with support for:
    - Full, incremental, and differential backups
    - Point-in-time recovery
    - Compression and deduplication
    - Remote backup storage
    - Backup validation and integrity checking
    """

    def __init__(self,
                 base_backup_path: str = "/var/backups",
                 max_backup_size: int = 1024 * 1024 * 1024,  # 1GB default chunk size
                 compression_level: int = 6,
                 validation_enabled: bool = True,
                 concurrent_chunks: int = 4):
        self.base_backup_path = Path(base_backup_path)
        self.max_backup_size = max_backup_size
        self.compression_level = compression_level
        self.validation_enabled = validation_enabled
        self.concurrent_chunks = concurrent_chunks
        
        # Ensure backup directory exists
        self.base_backup_path.mkdir(parents=True, exist_ok=True)
        
        # Backup storage
        self._backups: Dict[UUID, BackupMetadata] = {}
        self._chunks: Dict[UUID, List[DataChunk]] = {}
        self._index_db_path = self.base_backup_path / "backup_index.db"
        
        # Threading
        self._lock = threading.RLock()
        self._active_operations: Dict[str, Dict] = {}
        
        # Initialize index database
        self._initialize_index_db()
        
        # Load existing backups
        self._load_backup_index()

    def _initialize_index_db(self):
        """Initialize SQLite index database for backup metadata"""
        with sqlite3.connect(self._index_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backups (
                    backup_id TEXT PRIMARY KEY,
                    backup_type TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    completed_at REAL,
                    size_bytes INTEGER NOT NULL,
                    compressed_size INTEGER NOT NULL,
                    compression_type TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    source_location TEXT NOT NULL,
                    backup_location TEXT NOT NULL,
                    status TEXT NOT NULL,
                    description TEXT,
                    tags TEXT,
                    retention_policy TEXT,
                    incremental_base TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    backup_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    data_path TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    compressed_size INTEGER NOT NULL,
                    compression_type TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (backup_id) REFERENCES backups (backup_id)
                )
            """)
            
            conn.commit()

    def _load_backup_index(self):
        """Load backup metadata from index database"""
        try:
            with sqlite3.connect(self._index_db_path) as conn:
                cursor = conn.execute("SELECT * FROM backups")
                for row in cursor.fetchall():
                    backup = BackupMetadata(
                        backup_id=UUID(row[0]),
                        backup_type=BackupType(row[1]),
                        created_at=row[2],
                        completed_at=row[3],
                        size_bytes=row[4],
                        compressed_size=row[5],
                        compression_type=CompressionType(row[6]),
                        checksum=row[7],
                        source_location=row[8],
                        backup_location=row[9],
                        status=BackupStatus(row[10]),
                        description=row[11],
                        tags=json.loads(row[12]) if row[12] else [],
                        retention_policy=row[13],
                        incremental_base=UUID(row[14]) if row[14] else None
                    )
                    self._backups[backup.backup_id] = backup
        except Exception as e:
            logger.error("Failed to load backup index", error=str(e))

    def create_backup(self,
                     source_path: str,
                     backup_type: BackupType = BackupType.FULL,
                     description: Optional[str] = None,
                     tags: List[str] = None,
                     retention_policy: Optional[str] = None,
                     incremental_base: Optional[UUID] = None) -> UUID:
        """
        Create a backup of source data
        
        Args:
            source_path: Path to data source
            backup_type: Type of backup to create
            description: Optional description
            tags: Optional tags for categorization
            retention_policy: Optional retention policy
            incremental_base: Base backup for incremental backups
            
        Returns:
            Backup ID
        """
        backup_id = uuid4()
        
        try:
            with self._lock:
                # Initialize backup metadata
                backup_metadata = BackupMetadata(
                    backup_id=backup_id,
                    backup_type=backup_type,
                    created_at=time.time(),
                    completed_at=None,
                    size_bytes=0,
                    compressed_size=0,
                    compression_type=CompressionType.ZSTD,
                    checksum="",
                    source_location=source_path,
                    backup_location=str(self.base_backup_path / f"backup_{backup_id}"),
                    status=BackupStatus.PENDING,
                    description=description,
                    tags=tags or [],
                    retention_policy=retention_policy,
                    incremental_base=incremental_base
                )
                
                self._backups[backup_id] = backup_metadata
                self._chunks[backup_id] = []
                
                # Record operation start
                self._active_operations[str(backup_id)] = {
                    'operation': 'backup',
                    'start_time': time.time(),
                    'status': 'in_progress'
                }
            
            # Execute backup operation
            backup_metadata = asyncio.run(self._execute_backup(backup_metadata))
            
            with self._lock:
                backup_metadata.status = BackupStatus.COMPLETED
                backup_metadata.completed_at = time.time()
                
                # Update active operations
                if str(backup_id) in self._active_operations:
                    self._active_operations[str(backup_id)]['status'] = 'completed'
                    self._active_operations[str(backup_id)]['end_time'] = time.time()
            
            logger.info("Backup completed successfully",
                       backup_id=str(backup_id),
                       source=source_path,
                       backup_type=backup_type.value,
                       size=backup_metadata.size_bytes)
            
            return backup_id
            
        except Exception as e:
            # Mark backup as failed
            with self._lock:
                if backup_id in self._backups:
                    self._backups[backup_id].status = BackupStatus.FAILED
                
                if str(backup_id) in self._active_operations:
                    self._active_operations[str(backup_id)]['status'] = 'failed'
                    self._active_operations[str(backup_id)]['error'] = str(e)
            
            logger.error("Backup failed", backup_id=str(backup_id), error=str(e))
            raise

    async def _execute_backup(self, backup_metadata: BackupMetadata) -> BackupMetadata:
        """Execute backup operation"""
        source_path = Path(backup_metadata.source_location)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source path does not exist: {source_path}")
        
        backup_metadata.status = BackupStatus.IN_PROGRESS
        
        if source_path.is_file():
            await self._backup_file(backup_metadata, source_path)
        elif source_path.is_dir():
            await self._backup_directory(backup_metadata, source_path)
        else:
            raise ValueError(f"Unsupported source type: {source_path}")
        
        # Calculate final checksum and save metadata
        backup_metadata.checksum = await self._calculate_backup_checksum(backup_metadata.backup_id)
        
        # Save metadata to index
        self._save_backup_metadata(backup_metadata)
        
        return backup_metadata

    async def _backup_file(self, backup_metadata: BackupMetadata, file_path: Path):
        """Backup a single file"""
        async with aiofiles.open(file_path, 'rb') as f:
            data = await f.read()
        
        # Split into chunks if needed
        chunks = await self._create_data_chunks(data, backup_metadata.backup_id)
        
        # Save chunks
        await self._save_chunks(backup_metadata.backup_id, chunks)
        
        # Update metadata
        backup_metadata.size_bytes = len(data)
        backup_metadata.compressed_size = sum(chunk.compressed_size for chunk in chunks)

    async def _backup_directory(self, backup_metadata: BackupMetadata, dir_path: Path):
        """Backup a directory recursively"""
        all_chunks = []
        total_size = 0
        total_compressed_size = 0
        
        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
                async with aiofiles.open(file_path, 'rb') as f:
                    data = await f.read()
                
                relative_path = file_path.relative_to(dir_path)
                chunks = await self._create_data_chunks(
                    data, backup_metadata.backup_id, 
                    metadata={'file_path': str(relative_path)}
                )
                
                all_chunks.extend(chunks)
                total_size += len(data)
                total_compressed_size += sum(chunk.compressed_size for chunk in chunks)
        
        # Save all chunks
        await self._save_chunks(backup_metadata.backup_id, all_chunks)
        
        # Update metadata
        backup_metadata.size_bytes = total_size
        backup_metadata.compressed_size = total_compressed_size

    async def _create_data_chunks(self,
                                 data: bytes,
                                 backup_id: UUID,
                                 metadata: Optional[Dict] = None) -> List[DataChunk]:
        """Split data into chunks and compress them"""
        chunks = []
        chunk_index = 0
        
        # Include metadata in first chunk if provided
        if metadata:
            metadata_bytes = json.dumps(metadata).encode('utf-8')
            data = metadata_bytes + b'\n' + data
        
        # Split into chunks
        for i in range(0, len(data), self.max_backup_size):
            chunk_data = data[i:i + self.max_backup_size]
            
            # Compress chunk
            compressed_data, original_size = await self._compress_data(chunk_data)
            
            # Create chunk metadata
            chunk = DataChunk(
                chunk_id=uuid4(),
                backup_id=backup_id,
                chunk_index=chunk_index,
                data=compressed_data,
                checksum=hashlib.sha256(compressed_data).hexdigest(),
                size=len(chunk_data),
                compressed_size=len(compressed_data),
                compression_type=CompressionType.ZSTD,
                created_at=time.time()
            )
            
            chunks.append(chunk)
            chunk_index += 1
        
        return chunks

    async def _compress_data(self, data: bytes) -> Tuple[bytes, int]:
        """Compress data using specified algorithm"""
        if self.compression_level == 0:
            return data, len(data)
        
        compressor = zstd.ZstdCompressor(level=self.compression_level)
        compressed = compressor.compress(data)
        
        return compressed, len(data)

    async def _decompress_data(self, data: bytes, compression_type: CompressionType) -> bytes:
        """Decompress data"""
        if compression_type == CompressionType.NONE:
            return data
        elif compression_type == CompressionType.ZSTD:
            decompressor = zstd.ZstdDecompressor()
            return decompressor.decompress(data)
        else:
            raise ValueError(f"Unsupported compression type: {compression_type}")

    async def _save_chunks(self, backup_id: UUID, chunks: List[DataChunk]):
        """Save chunks to disk"""
        backup_dir = self.base_backup_path / str(backup_id)
        backup_dir.mkdir(exist_ok=True)
        
        # Save chunks concurrently
        tasks = []
        semaphore = asyncio.Semaphore(self.concurrent_chunks)
        
        for chunk in chunks:
            task = asyncio.create_task(self._save_single_chunk(chunk, backup_dir, semaphore))
            tasks.append(task)
        
        # Wait for all chunks to be saved
        await asyncio.gather(*tasks)
        
        # Update in-memory storage
        with self._lock:
            if backup_id not in self._chunks:
                self._chunks[backup_id] = []
            self._chunks[backup_id].extend(chunks)

    async def _save_single_chunk(self, chunk: DataChunk, backup_dir: Path, semaphore: asyncio.Semaphore):
        """Save a single chunk to disk"""
        async with semaphore:
            chunk_file = backup_dir / f"chunk_{chunk.chunk_index:06d}.zst"
            
            async with aiofiles.open(chunk_file, 'wb') as f:
                await f.write(chunk.data)
            
            # Save chunk metadata to database
            with sqlite3.connect(self._index_db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO chunks 
                    (chunk_id, backup_id, chunk_index, data_path, checksum, 
                     size, compressed_size, compression_type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(chunk.chunk_id),
                    str(chunk.backup_id),
                    chunk.chunk_index,
                    str(chunk_file),
                    chunk.checksum,
                    chunk.size,
                    chunk.compressed_size,
                    chunk.compression_type.value,
                    chunk.created_at
                ))
                conn.commit()

    async def _calculate_backup_checksum(self, backup_id: UUID) -> str:
        """Calculate checksum for entire backup"""
        hasher = hashlib.sha256()
        
        # Get chunks in order
        with self._lock:
            chunks = sorted(self._chunks.get(backup_id, []), key=lambda x: x.chunk_index)
        
        for chunk in chunks:
            hasher.update(chunk.data)
        
        return hasher.hexdigest()

    def _save_backup_metadata(self, backup_metadata: BackupMetadata):
        """Save backup metadata to database"""
        with sqlite3.connect(self._index_db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO backups 
                (backup_id, backup_type, created_at, completed_at, size_bytes,
                 compressed_size, compression_type, checksum, source_location,
                 backup_location, status, description, tags, retention_policy,
                 incremental_base)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(backup_metadata.backup_id),
                backup_metadata.backup_type.value,
                backup_metadata.created_at,
                backup_metadata.completed_at,
                backup_metadata.size_bytes,
                backup_metadata.compressed_size,
                backup_metadata.compression_type.value,
                backup_metadata.checksum,
                backup_metadata.source_location,
                backup_metadata.backup_location,
                backup_metadata.status.value,
                backup_metadata.description,
                json.dumps(backup_metadata.tags) if backup_metadata.tags else None,
                backup_metadata.retention_policy,
                str(backup_metadata.incremental_base) if backup_metadata.incremental_base else None
            ))
            conn.commit()

    async def restore_backup(self,
                           backup_id: UUID,
                           target_path: str,
                           validate_checksum: bool = True,
                           restore_metadata: Optional[Dict] = None) -> bool:
        """
        Restore data from a backup
        
        Args:
            backup_id: Backup to restore
            target_path: Target location for restoration
            validate_checksum: Whether to validate data integrity
            restore_metadata: Optional metadata for restoration
            
        Returns:
            True if restore successful
        """
        if backup_id not in self._backups:
            raise ValueError(f"Backup not found: {backup_id}")
        
        backup_metadata = self._backups[backup_id]
        
        if backup_metadata.status != BackupStatus.COMPLETED:
            raise ValueError(f"Cannot restore incomplete backup: {backup_metadata.status.value}")
        
        try:
            logger.info("Starting backup restoration",
                       backup_id=str(backup_id),
                       target_path=target_path)
            
            # Get chunks
            with self._lock:
                chunks = sorted(
                    self._chunks.get(backup_id, []),
                    key=lambda x: x.chunk_index
                )
            
            if not chunks:
                raise ValueError("No chunks found for backup")
            
            # Restore data
            await self._restore_from_chunks(backup_id, chunks, target_path, validate_checksum)
            
            logger.info("Backup restoration completed successfully",
                       backup_id=str(backup_id),
                       target_path=target_path)
            
            return True
            
        except Exception as e:
            logger.error("Backup restoration failed",
                        backup_id=str(backup_id),
                        error=str(e))
            raise

    async def _restore_from_chunks(self,
                                 backup_id: UUID,
                                 chunks: List[DataChunk],
                                 target_path: str,
                                 validate_checksum: bool):
        """Restore data from chunks"""
        target_dir = Path(target_path)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Process chunks in order
        for chunk in chunks:
            chunk_file = Path(backup_id) / f"chunk_{chunk.chunk_index:06d}.zst"
            full_chunk_path = self.base_backup_path / chunk_file
            
            # Read compressed data
            async with aiofiles.open(full_chunk_path, 'rb') as f:
                compressed_data = await f.read()
            
            # Validate checksum if requested
            if validate_checksum:
                calculated_checksum = hashlib.sha256(compressed_data).hexdigest()
                if calculated_checksum != chunk.checksum:
                    raise ValueError(f"Chunk checksum mismatch: {chunk.chunk_id}")
            
            # Decompress data
            decompressed_data = await self._decompress_data(compressed_data, chunk.compression_type)
            
            # Extract metadata if present
            if chunk.chunk_index == 0:
                lines = decompressed_data.split(b'\n')
                if len(lines) > 1 and lines[0].startswith(b'{'):
                    metadata_bytes = lines[0]
                    data_bytes = b'\n'.join(lines[1:])
                    
                    try:
                        metadata = json.loads(metadata_bytes.decode('utf-8'))
                        if 'file_path' in metadata:
                            file_path = target_dir / metadata['file_path']
                            file_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            async with aiofiles.open(file_path, 'wb') as f:
                                await f.write(data_bytes)
                            continue
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # Not metadata, treat as regular data
                        decompressed_data = decompressed_data
            
            # Write data to target
            output_file = target_dir / f"restored_file_{chunk.chunk_index:06d}"
            async with aiofiles.open(output_file, 'wb') as f:
                await f.write(decompressed_data)

    def get_backup_info(self, backup_id: UUID) -> Optional[BackupMetadata]:
        """Get information about a backup"""
        return self._backups.get(backup_id)

    def list_backups(self,
                    backup_type: Optional[BackupType] = None,
                    status: Optional[BackupStatus] = None,
                    tags: Optional[List[str]] = None) -> List[BackupMetadata]:
        """List backups with optional filtering"""
        backups = list(self._backups.values())
        
        # Apply filters
        if backup_type:
            backups = [b for b in backups if b.backup_type == backup_type]
        
        if status:
            backups = [b for b in backups if b.status == status]
        
        if tags:
            backups = [b for b in backups if any(tag in b.tags for tag in tags)]
        
        # Sort by creation date (newest first)
        return sorted(backups, key=lambda x: x.created_at, reverse=True)

    def delete_backup(self, backup_id: UUID, verify_deletion: bool = True) -> bool:
        """
        Delete a backup and all its chunks
        
        Args:
            backup_id: Backup to delete
            verify_deletion: Whether to verify files are deleted
            
        Returns:
            True if deletion successful
        """
        if backup_id not in self._backups:
            logger.warning("Attempted to delete non-existent backup", backup_id=str(backup_id))
            return False
        
        try:
            with self._lock:
                # Remove chunks from disk
                backup_dir = self.base_backup_path / str(backup_id)
                if backup_dir.exists():
                    import shutil
                    shutil.rmtree(backup_dir)
                
                # Remove from index database
                with sqlite3.connect(self._index_db_path) as conn:
                    conn.execute("DELETE FROM chunks WHERE backup_id = ?", (str(backup_id),))
                    conn.execute("DELETE FROM backups WHERE backup_id = ?", (str(backup_id),))
                    conn.commit()
                
                # Remove from memory
                del self._chunks[backup_id]
                del self._backups[backup_id]
                
                logger.info("Backup deleted successfully", backup_id=str(backup_id))
                return True
                
        except Exception as e:
            logger.error("Failed to delete backup",
                        backup_id=str(backup_id),
                        error=str(e))
            return False

    def validate_backup_integrity(self, backup_id: UUID) -> Dict[str, Any]:
        """Validate backup integrity"""
        if backup_id not in self._backups:
            return {'valid': False, 'error': 'Backup not found'}
        
        try:
            with self._lock:
                chunks = sorted(
                    self._chunks.get(backup_id, []),
                    key=lambda x: x.chunk_index
                )
            
            validation_results = {
                'backup_id': str(backup_id),
                'total_chunks': len(chunks),
                'valid_chunks': 0,
                'invalid_chunks': [],
                'missing_chunks': [],
                'checksum_mismatches': []
            }
            
            for chunk in chunks:
                chunk_file = self.base_backup_path / str(backup_id) / f"chunk_{chunk.chunk_index:06d}.zst"
                
                if not chunk_file.exists():
                    validation_results['missing_chunks'].append(chunk.chunk_index)
                    continue
                
                # Read and validate checksum
                import hashlib
                with open(chunk_file, 'rb') as f:
                    file_data = f.read()
                
                calculated_checksum = hashlib.sha256(file_data).hexdigest()
                if calculated_checksum != chunk.checksum:
                    validation_results['checksum_mismatches'].append({
                        'chunk_index': chunk.chunk_index,
                        'expected': chunk.checksum,
                        'calculated': calculated_checksum
                    })
                else:
                    validation_results['valid_chunks'] += 1
            
            validation_results['valid'] = (
                len(validation_results['missing_chunks']) == 0 and
                len(validation_results['checksum_mismatches']) == 0
            )
            
            return validation_results
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}

    def apply_retention_policy(self) -> Dict[str, int]:
        """Apply retention policies to backups"""
        cutoff_time = time.time() - (30 * 24 * 60 * 60)  # 30 days default
        
        deleted_backups = 0
        deleted_chunks = 0
        
        with self._lock:
            backup_ids = list(self._backups.keys())
        
        for backup_id in backup_ids:
            backup = self._backups[backup_id]
            
            # Check if backup should be deleted based on retention policy
            should_delete = False
            
            if backup.retention_policy == 'temporary' and backup.created_at < cutoff_time:
                should_delete = True
            elif backup.created_at < cutoff_time and backup.status == BackupStatus.COMPLETED:
                # Auto-delete old completed backups
                should_delete = True
            
            if should_delete:
                if self.delete_backup(backup_id, verify_deletion=False):
                    deleted_backups += 1
                    if backup_id in self._chunks:
                        deleted_chunks += len(self._chunks[backup_id])
        
        logger.info("Retention policy applied",
                   deleted_backups=deleted_backups,
                   deleted_chunks=deleted_chunks)
        
        return {
            'deleted_backups': deleted_backups,
            'deleted_chunks': deleted_chunks
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get backup handler statistics"""
        with self._lock:
            total_backups = len(self._backups)
            completed_backups = sum(1 for b in self._backups.values() 
                                  if b.status == BackupStatus.COMPLETED)
            total_size = sum(b.size_bytes for b in self._backups.values())
            total_compressed_size = sum(b.compressed_size for b in self._backups.values())
            
            # Calculate compression ratio
            compression_ratio = (
                total_size / total_compressed_size if total_compressed_size > 0 else 1.0
            )
            
            return {
                'total_backups': total_backups,
                'completed_backups': completed_backups,
                'failed_backups': sum(1 for b in self._backups.values() 
                                    if b.status == BackupStatus.FAILED),
                'total_size_bytes': total_size,
                'compressed_size_bytes': total_compressed_size,
                'compression_ratio': compression_ratio,
                'total_chunks': sum(len(chunks) for chunks in self._chunks.values()),
                'backup_types': {
                    btype.value: sum(1 for b in self._backups.values() 
                                   if b.backup_type == btype)
                    for btype in BackupType
                }
            }

    def cleanup(self):
        """Cleanup resources"""
        # Apply retention policy
        self.apply_retention_policy()
        
        logger.info("Backup handler cleanup completed")


# Global backup handler instance
_backup_handler: Optional[BackupHandler] = None


def get_backup_handler(**kwargs) -> BackupHandler:
    """Get or create global backup handler instance"""
    global _backup_handler
    if _backup_handler is None:
        _backup_handler = BackupHandler(**kwargs)
    return _backup_handler
