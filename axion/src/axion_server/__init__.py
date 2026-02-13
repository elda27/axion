"""Axion Server - API and database components

New module structure:
- shared/kernel: Database engine, session management
- shared/libs: Configuration and utilities
- shared/domain: Pydantic schemas (request/response models)
- repos: SQLAlchemy repositories and models
- gateways: External service integrations (object storage)
- ops: Background operations (DP runner)
- apps: FastAPI application and API routers
"""

__version__ = "0.1.0"
