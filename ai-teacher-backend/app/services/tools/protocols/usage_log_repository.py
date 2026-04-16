"""Protocol for usage log repository operations.

This module defines the interface for usage log repository implementations.
"""

from typing import Protocol

from app.models.resource import ToolUsageLog


class UsageLogRepositoryProtocol(Protocol):
    """Protocol for usage log repository operations.
    
    This interface defines the contract for usage logging.
    Any class that implements these methods can be used as a usage log repository.
    
    Implementations:
        - ToolUsageLogRepository: In-memory storage implementation
        - DatabaseUsageLogRepository: Database storage implementation (future)
    
    Example:
        >>> class MyUsageLogRepository(UsageLogRepositoryProtocol):
        ...     def create(self, log: ToolUsageLog) -> ToolUsageLog:
        ...         if not log.id:
        ...             log.id = str(uuid.uuid4())
        ...         log.created_at = datetime.now()
        ...         self._logs.append(log)
        ...         return log
    """

    def create(self, log: ToolUsageLog) -> ToolUsageLog:
        """Create usage log entry.
        
        Args:
            log: Tool usage log entry to create.
                - id: Will be auto-generated if not provided
                - tool_name: Name of the tool
                - knowledge_point_id: Knowledge point ID
                - student_id: Student ID (optional)
                - action: Action performed
                - params: Action parameters
                - result: Action result
                - success: Whether action succeeded
                - execution_time_ms: Execution time in milliseconds
        
        Returns:
            Created log entry with generated ID and timestamp.
        
        Raises:
            DatabaseError: If log creation fails.
        """
        ...
