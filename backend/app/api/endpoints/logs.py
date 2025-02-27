from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
import os
import json
from datetime import datetime
from ...services.auth import get_current_active_user
from ...models.user import User
import logging
from ...services.search import SearchService

router = APIRouter()
logger = logging.getLogger(__name__)

# Directory where logs are stored
LOGS_DIR = os.environ.get("LOGS_DIR", "logs")
search_service = SearchService()

@router.get("/")
async def get_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    level: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Get paginated logs with optional filtering.
    Returns only basic log information for the list view.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to view logs")
    
    try:
        # Ensure logs directory exists
        if not os.path.exists(LOGS_DIR):
            return {"total": 0, "page": page, "per_page": per_page, "logs": []}
        
        # Get all log files
        log_files = [f for f in os.listdir(LOGS_DIR) if f.endswith('.json')]
        log_files.sort(reverse=True)  # Most recent first
        
        # Calculate pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        # Process logs with pagination and filtering
        logs = []
        total_matching = 0
        
        for file_name in log_files:
            try:
                file_path = os.path.join(LOGS_DIR, file_name)
                
                # Read only the first 4KB of the file to extract basic info
                # This avoids loading the entire file into memory
                with open(file_path, 'r') as f:
                    # Read first 4KB which should contain the basic metadata
                    file_start = f.read(4096)
                    
                    # Try to extract just the basic fields we need
                    try:
                        # Find the positions of key fields in the JSON
                        id_pos = file_start.find('"id"')
                        timestamp_pos = file_start.find('"timestamp"')
                        level_pos = file_start.find('"level"')
                        message_pos = file_start.find('"message"')
                        path_pos = file_start.find('"path"')
                        method_pos = file_start.find('"method"')
                        status_code_pos = file_start.find('"status_code"')
                        ip_pos = file_start.find('"ip"')
                        duration_pos = file_start.find('"duration_ms"')
                        
                        # Extract values using string operations instead of parsing the whole JSON
                        def extract_value(pos):
                            if pos == -1:
                                return None
                            
                            # Find the value after the colon
                            value_start = file_start.find(':', pos) + 1
                            # Skip whitespace
                            while value_start < len(file_start) and file_start[value_start].isspace():
                                value_start += 1
                                
                            # Check if it's a string (starts with ")
                            if file_start[value_start] == '"':
                                value_end = file_start.find('"', value_start + 1)
                                return file_start[value_start+1:value_end]
                            else:
                                # For numbers, booleans, etc.
                                value_end = file_start.find(',', value_start)
                                if value_end == -1:
                                    value_end = file_start.find('}', value_start)
                                if value_end == -1:
                                    return None
                                return file_start[value_start:value_end].strip()
                        
                        # Extract basic fields
                        log_id = extract_value(id_pos) or file_name.replace(".json", "")
                        timestamp = extract_value(timestamp_pos)
                        level = extract_value(level_pos)
                        message = extract_value(message_pos)
                        path = extract_value(path_pos)
                        method = extract_value(method_pos)
                        status_code = extract_value(status_code_pos)
                        ip = extract_value(ip_pos)
                        duration_ms = extract_value(duration_pos)
                        
                        # If we couldn't extract the fields, fall back to parsing the whole file
                        if not (timestamp and level and message):
                            # If we couldn't extract the basic fields, read the whole file
                            f.seek(0)
                            log_data = json.load(f)
                            log_id = log_data.get("id", file_name.replace(".json", ""))
                            timestamp = log_data.get("timestamp")
                            level = log_data.get("level")
                            message = log_data.get("message")
                            path = log_data.get("path")
                            method = log_data.get("method")
                            status_code = log_data.get("status_code")
                            ip = log_data.get("ip")
                            duration_ms = log_data.get("duration_ms")
                    except:
                        # If string extraction fails, fall back to parsing the whole file
                        f.seek(0)
                        log_data = json.load(f)
                        log_id = log_data.get("id", file_name.replace(".json", ""))
                        timestamp = log_data.get("timestamp")
                        level = log_data.get("level")
                        message = log_data.get("message")
                        path = log_data.get("path")
                        method = log_data.get("method")
                        status_code = log_data.get("status_code")
                        ip = log_data.get("ip")
                        duration_ms = log_data.get("duration_ms")
                
                # Apply level filter if specified
                if level and level.lower() != (level or "").lower():
                    continue
                
                # Apply search filter if specified
                if search:
                    search_lower = search.lower()
                    # Check if search term is in any of these fields
                    search_fields = [
                        message or "",
                        path or "",
                        method or "",
                        ip or "",
                        str(status_code or ""),
                    ]
                    if not any(search_lower in str(field).lower() for field in search_fields):
                        continue
                
                # Count total matching logs
                total_matching += 1
                
                # Only include logs within the current page
                if total_matching > start_idx and total_matching <= end_idx:
                    # Create a summary version of the log with only essential fields
                    log_summary = {
                        "id": log_id,
                        "timestamp": timestamp,
                        "level": level,
                        "message": message,
                        "path": path,
                        "method": method,
                        "status_code": status_code,
                        "ip": ip,
                        "duration_ms": duration_ms,
                    }
                    logs.append(log_summary)
            except Exception as e:
                logger.error(f"Error processing log file {file_name}: {str(e)}")
        
        return {
            "total": total_matching,
            "page": page,
            "per_page": per_page,
            "logs": logs
        }
    
    except Exception as e:
        logger.error(f"Error retrieving logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")

@router.get("/logs/{process_id}")
async def get_log_details(
    process_id: str,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    try:
        # Get the log
        log = await search_service.get_log(process_id)
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")

        # If it's a bulk search, get child logs
        if log.get("query") == "BULK_SEARCH":
            child_logs = await search_service.get_child_logs(process_id)
            log["children"] = child_logs

        return log
    except Exception as e:
        logger.error(f"Error retrieving log details: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving log details: {str(e)}"
        )

@router.get("/export")
async def export_logs(
    current_user: User = Depends(get_current_active_user),
    level: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Export all logs matching the filter criteria.
    This is a separate endpoint for downloading all logs.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to export logs")
    
    try:
        # Ensure logs directory exists
        if not os.path.exists(LOGS_DIR):
            return []
        
        # Parse date filters if provided
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        
        # Get all log files
        log_files = [f for f in os.listdir(LOGS_DIR) if f.endswith('.json')]
        log_files.sort(reverse=True)  # Most recent first
        
        # Process all logs with filtering
        logs = []
        
        for file_name in log_files:
            try:
                file_path = os.path.join(LOGS_DIR, file_name)
                with open(file_path, 'r') as f:
                    log_data = json.load(f)
                
                # Apply level filter if specified
                if level and log_data.get('level', '').lower() != level.lower():
                    continue
                
                # Apply search filter if specified
                if search:
                    search_lower = search.lower()
                    # Check if search term is in any of these fields
                    search_fields = [
                        log_data.get('message', ''),
                        log_data.get('path', ''),
                        log_data.get('method', ''),
                        log_data.get('ip', ''),
                        log_data.get('user_agent', ''),
                        str(log_data.get('status_code', '')),
                    ]
                    if not any(search_lower in str(field).lower() for field in search_fields):
                        continue
                
                # Apply date filters if specified
                if start_datetime or end_datetime:
                    log_timestamp = log_data.get('timestamp')
                    if log_timestamp:
                        try:
                            log_datetime = datetime.fromisoformat(log_timestamp.replace('Z', '+00:00'))
                            if start_datetime and log_datetime < start_datetime:
                                continue
                            if end_datetime and log_datetime > end_datetime:
                                continue
                        except ValueError:
                            continue
                
                logs.append(log_data)
            except Exception as e:
                logger.error(f"Error processing log file {file_name} for export: {str(e)}")
        
        return logs
    
    except Exception as e:
        logger.error(f"Error exporting logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting logs: {str(e)}")

@router.get("/bulk-search/logs/{process_id}")
async def get_bulk_search_details(
    process_id: str,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    try:
        # Get the main bulk search log
        bulk_log = await search_service.get_log(process_id)
        if not bulk_log:
            raise HTTPException(status_code=404, detail="Bulk search log not found")

        # Get all child logs for this bulk search
        child_logs = await search_service.get_child_logs(process_id)
        
        return {
            "log": bulk_log,
            "children": child_logs
        }
    except Exception as e:
        logger.error(f"Error retrieving bulk search details: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving bulk search details: {str(e)}"
        ) 