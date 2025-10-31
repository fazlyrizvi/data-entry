"""
Example: RBAC Security Integration

This example demonstrates how to integrate the RBAC security system
into a FastAPI application with various endpoints and security controls.
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os

# Import RBAC components
from code.security.rbac.auth_middleware import get_auth_middleware
from code.security.rbac.permission_guard import (
    get_permission_guard,
    PermissionGroups,
    PermissionContext,
    ResourceType
)
from code.security.rbac.session_manager import get_session_manager

# Import Supabase client
from supabase import create_client

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL", "https://your-project.supabase.co"),
    os.getenv("SUPABASE_ANON_KEY", "your-anon-key")
)

# Initialize RBAC components
auth = get_auth_middleware()
guard = get_permission_guard(supabase)
session_manager = get_session_manager(supabase)

# Initialize FastAPI app
app = FastAPI(title="RBAC Security Example")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Request/Response Models
class LoginRequest(BaseModel):
    email: str
    password: str

class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    classification_level: str = "INTERNAL"

class UserCreate(BaseModel):
    email: str
    password: str
    roles: List[str]

# Authentication Endpoints

@app.post("/auth/login")
async def login(request: Request, login_data: LoginRequest):
    """User login with authentication and security checks."""
    try:
        result = await auth.login(
            email=login_data.email,
            password=login_data.password,
            request=request
        )
        
        # Set session cookie
        response = JSONResponse(content=result)
        await session_manager.set_session_cookie(response, result["access_token"])
        
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@app.post("/auth/logout")
async def logout(request: Request):
    """User logout with session invalidation."""
    user = request.state.user
    
    # Invalidate all user sessions
    await session_manager.invalidate_all_user_sessions(user.user_id)
    
    response = JSONResponse(content={"message": "Successfully logged out"})
    await session_manager.clear_session_cookie(response)
    
    return response

@app.post("/auth/refresh")
async def refresh_session(request: Request):
    """Refresh session token."""
    token = request.cookies.get("session_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session token found"
        )
    
    # Validate current session
    session_info = await session_manager.validate_session_token(token)
    if not session_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    # Generate new token
    new_token = await session_manager.refresh_session(session_info.session_id)
    
    if not new_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cannot refresh session"
        )
    
    response = JSONResponse(content={"access_token": new_token})
    await session_manager.set_session_cookie(response, new_token)
    
    return response

# Dataset Endpoints

@app.get("/datasets")
async def list_datasets(
    request: Request,
    user = Depends(auth.requires_permissions(["dataset:read"]))
):
    """List all datasets - requires dataset:read permission."""
    try:
        # Query datasets from database
        response = supabase.table("datasets").select("*").execute()
        
        return {
            "datasets": response.data,
            "count": len(response.data),
            "user": {
                "id": user.user_id,
                "roles": user.roles
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/datasets")
async def create_dataset(
    request: Request,
    dataset: DatasetCreate,
    user = Depends(auth.require_permissions(PermissionGroups.DATASET_WRITE))
):
    """Create new dataset - requires dataset:write permission."""
    try:
        # Create dataset in database
        new_dataset = supabase.table("datasets").insert({
            "name": dataset.name,
            "description": dataset.description,
            "classification_level": dataset.classification_level,
            "owner_id": user.user_id,
            "created_by": user.user_id
        }).execute()
        
        return {
            "message": "Dataset created successfully",
            "dataset": new_dataset.data[0]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/datasets/{dataset_id}")
async def get_dataset(
    request: Request,
    dataset_id: str,
    user = Depends(auth.require_permissions(["dataset:read"]))
):
    """Get specific dataset with ownership check."""
    try:
        # Check resource ownership
        context = PermissionContext(
            resource_id=dataset_id,
            data_classification="CONFIDENTIAL",
            is_critical_operation=False
        )
        
        # Verify user has access to this resource
        has_access = await guard.checker.check_resource_ownership(
            user.user_id,
            dataset_id,
            ResourceType.DATASET,
            context
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this dataset"
            )
        
        # Get dataset
        response = supabase.table("datasets").select("*").eq("id", dataset_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        return {
            "dataset": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.delete("/datasets/{dataset_id}")
async def delete_dataset(
    request: Request,
    dataset_id: str,
    user = Depends(auth.require_permissions(PermissionGroups.DATASET_ADMIN))
):
    """Delete dataset - requires admin permissions."""
    try:
        # Check SoD constraints
        is_valid = await guard.check_separation_of_duties(
            user_id=user.user_id,
            requested_action="dataset:delete"
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Separation of duties constraint violation"
            )
        
        # Delete dataset
        supabase.table("datasets").delete().eq("id", dataset_id).execute()
        
        return {
            "message": "Dataset deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Pipeline Endpoints

@app.get("/pipelines")
async def list_pipelines(
    request: Request,
    user = Depends(auth.require_permissions(PermissionGroups.PIPELINE_EXECUTE))
):
    """List pipelines - requires execute permission."""
    try:
        response = supabase.table("pipelines").select("*").execute()
        
        return {
            "pipelines": response.data,
            "count": len(response.data)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/pipelines/{pipeline_id}/execute")
async def execute_pipeline(
    request: Request,
    pipeline_id: str,
    user = Depends(auth.require_roles(["OPERATOR", "MANAGER", "ADMIN"]))
):
    """Execute pipeline - requires OPERATOR role or higher."""
    try:
        # Check ownership
        @auth.require_resource_ownership(ResourceType.PIPELINE, "pipeline_id")
        async def execute_pipeline_logic():
            # Execute pipeline logic here
            return {"status": "executed", "pipeline_id": pipeline_id}
        
        return await execute_pipeline_logic()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# User Management Endpoints (Admin Only)

@app.get("/users")
async def list_users(
    request: Request,
    user = Depends(auth.require_permissions(PermissionGroups.USER_READ))
):
    """List users - requires user:read permission."""
    try:
        response = supabase.table("users").select("id, email, created_at").execute()
        
        return {
            "users": response.data,
            "count": len(response.data)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/users")
async def create_user(
    request: Request,
    user_data: UserCreate,
    user = Depends(auth.require_permissions(PermissionGroups.USER_MANAGE))
):
    """Create new user - requires user:manage permission."""
    try:
        # Check SoD constraints
        is_valid = await guard.check_separation_of_duties(
            user_id=user.user_id,
            requested_action="user:create"
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="SoD constraint violation"
            )
        
        # Create user logic here
        # This would typically involve Supabase auth user creation
        
        return {
            "message": "User created successfully",
            "user": {
                "email": user_data.email,
                "roles": user_data.roles
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# System Administration Endpoints

@app.get("/audit/logs")
async def get_audit_logs(
    request: Request,
    limit: int = 100,
    user = Depends(auth.require_permissions(PermissionGroups.AUDIT_READ))
):
    """Get audit logs - requires audit:read permission."""
    try:
        response = supabase.rpc("audit.get_recent_events", {
            "p_limit": limit
        }).execute()
        
        return {
            "logs": response.data,
            "count": len(response.data)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/admin/system-status")
async def system_status(
    request: Request,
    user = Depends(auth.require_permissions(PermissionGroups.SYSTEM_ADMIN))
):
    """Get system status - requires admin permission."""
    try:
        # Check session count
        sessions = await session_manager.list_user_sessions(user.user_id)
        
        # Get user permissions
        permissions = await guard.get_user_permissions(user.user_id)
        
        return {
            "status": "healthy",
            "active_sessions": len(sessions),
            "user_permissions": permissions,
            "system_time": "2025-10-31T19:16:02Z"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Public Endpoint (No Authentication Required)

@app.get("/public/info")
async def public_info():
    """Public information endpoint - no authentication required."""
    return {
        "service": "RBAC Security Example",
        "version": "1.0.0",
        "status": "operational",
        "security": "Enabled with RBAC"
    }

# Error Handler

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global error handler for HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": "2025-10-31T19:16:02Z"
            }
        }
    )

# Middleware for Request Logging

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for security monitoring."""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    # Log request (in production, use proper logging)
    print(f"""
    Request: {request.method} {request.url.path}
    Status: {response.status_code}
    Duration: {process_time:.4f}s
    IP: {request.client.host if request.client else 'unknown'}
    """)
    
    return response

# Health Check

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2025-10-31T19:16:02Z",
        "checks": {
            "database": "ok",
            "redis": "ok",
            "security": "enabled"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
