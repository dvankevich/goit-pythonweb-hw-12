Configuration
=============

This section contains documentation for all application configuration settings and management.

.. toctree::
   :maxdepth: 2
   :caption: Configuration Modules

   app_config

Overview
--------

The configuration layer manages all application settings including:

* **Database Configuration**: PostgreSQL connection settings and URLs
* **Authentication**: JWT secrets, algorithms, and expiration settings
* **Email Services**: SMTP configuration for Brevo email service
* **Cloud Storage**: Cloudinary integration settings
* **Caching**: Redis configuration and connection settings
* **Security**: CORS origins and admin user credentials
* **Logging**: Application log level and debugging settings

Features
---------

* **Environment-based Configuration**: Settings loaded from .env files
* **Secret Management**: Sensitive data protected with SecretStr
* **Validation**: Automatic validation of configuration values
* **Type Safety**: Full type hints and Pydantic integration
* **Debug Support**: Configuration display utilities for development

All configuration is managed through the Settings class which provides
property methods for derived values like database URLs and CORS lists.
