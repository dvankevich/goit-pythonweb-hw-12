Services
=========

This section contains documentation for all service classes that handle business logic and external integrations.

.. toctree::
   :maxdepth: 2
   :caption: Services

   auth
   email
   upload_file
   users

Overview
--------

Service classes provide the business logic layer between the API endpoints and the repositories. They handle:

* **Authentication Service**: JWT token management, password hashing, and user authentication
* **Email Service**: Email notifications with HTML templates and fallback mechanisms
* **File Upload Service**: Cloudinary integration for avatar uploads
* **User Service**: User management operations with Gravatar integration

Each service encapsulates specific business logic and provides a clean interface for the API layer to interact with, ensuring separation of concerns and maintainable code architecture.
