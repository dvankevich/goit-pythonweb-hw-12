Database
========

This section contains documentation for database configuration, connection management, and caching components.

.. toctree::
   :maxdepth: 2
   :caption: Database Modules

   base
   redis_client
   session

Overview
--------

The database layer provides the foundation for all data persistence and caching operations:

* **Base**: SQLAlchemy declarative base class for all models
* **Redis Client**: Asynchronous Redis connection management and caching utilities
* **Session**: Database session management for FastAPI dependency injection

These components handle database connections, caching, session management, and provide the infrastructure for all data operations throughout the application.
