"""
Database connectivity utilities and health checks
"""

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .database import SessionLocal
from .schemas import DatabaseStatus

logger = logging.getLogger(__name__)


def check_database_connectivity() -> DatabaseStatus:
    """
    Check if database is accessible and responsive.

    Returns DatabaseStatus with connection status and any error details.
    """
    try:
        db = SessionLocal()
        try:
            # Simple query to test connectivity
            result = db.execute(text("SELECT 1"))
            result.fetchone()

            logger.info("Database connectivity check passed")
            return DatabaseStatus(connected=True)

        finally:
            db.close()

    except SQLAlchemyError as e:
        error_msg = f"Database connection failed: {e!s}"
        logger.error(error_msg)
        return DatabaseStatus(connected=False, error=error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during database check: {e!s}"
        logger.error(error_msg)
        return DatabaseStatus(connected=False, error=error_msg)


def check_database_connectivity_with_session(db: Session) -> DatabaseStatus:
    """
    Check database connectivity using provided session (for use in endpoints).

    This version respects dependency injection overrides used in tests.
    """
    try:
        # Simple query to test connectivity
        result = db.execute(text("SELECT 1"))
        result.fetchone()

        logger.info("Database connectivity check passed")
        return DatabaseStatus(connected=True)

    except SQLAlchemyError as e:
        error_msg = f"Database connection failed: {e!s}"
        logger.error(error_msg)
        return DatabaseStatus(connected=False, error=error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during database check: {e!s}"
        logger.error(error_msg)
        return DatabaseStatus(connected=False, error=error_msg)


def ensure_database_connectivity() -> None:
    """
    Ensure database is accessible on startup.

    Raises exception if database is not available - fail fast principle.
    """
    db_status = check_database_connectivity()

    if not db_status.connected:
        error_msg = f"Database connectivity check failed on startup: {db_status.error}"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)

    logger.info("✅ Database connectivity verified on startup")
