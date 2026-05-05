API Endpoints
=============

This section contains documentation for all FastAPI endpoints and route handlers.

.. toctree::
   :maxdepth: 2
   :caption: API Modules

   auth
   contact_api
   health
   users

Overview
--------

The API layer provides RESTful endpoints for all application functionality:

* **Authentication API**: User registration, login, email verification, and password management
* **Contact API**: CRUD operations for contact management with filtering and search
* **Health API**: System health monitoring and status checking
* **Users API**: User profile management and avatar updates

All endpoints include proper authentication, rate limiting, error handling, and comprehensive documentation through FastAPI's automatic OpenAPI generation.
