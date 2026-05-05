Schemas
=======

This section contains documentation for all Pydantic schemas used for data validation and serialization.

.. toctree::
   :maxdepth: 2
   :caption: Schemas

   contact
   user

Overview
--------

Pydantic schemas are used throughout the application to:

* **Validate incoming data**: Ensure data meets required constraints and types
* **Serialize responses**: Convert database objects to JSON-serializable formats
* **Document API contracts**: Define the structure of request/response data

The schemas are organized by domain:

* **Contact Schemas**: Handle contact data validation and serialization
* **User Schemas**: Manage user authentication, registration, and profile data

Each schema includes comprehensive field validation, type hints, and Google-style docstrings for clear documentation.
