Contacts Management API (FastAPI) documentation
===============================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   config/index
   api/index
   db/index
   repositories/index
   models/index
   schemas/index
   services/index
   utils/index

Main Application
================

.. automodule:: main
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Application Overview
--------------------

The main FastAPI application provides a complete RESTful API for contact management with:

* **Authentication**: JWT-based user authentication with email verification
* **Contact Management**: Full CRUD operations with advanced filtering and search
* **Rate Limiting**: Protection against API abuse with configurable limits
* **Caching**: Redis integration for improved performance
* **File Upload**: Cloudinary integration for avatar images
* **Health Monitoring**: System status and health check endpoints
* **Documentation**: Automatic OpenAPI/Swagger and ReDoc documentation

Key Components
~~~~~~~~~~~~~~

* **lifespan**: Application lifecycle management for Redis connections
* **rate_limit_handler**: Custom error handling for rate limit violations
* **root**: Welcome endpoint with API information
* **CORS Middleware**: Cross-origin request handling
* **Router Integration**: Organized API endpoints by functionality

The application follows modern FastAPI best practices with async/await support,
dependency injection, comprehensive error handling, and automatic API documentation.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`