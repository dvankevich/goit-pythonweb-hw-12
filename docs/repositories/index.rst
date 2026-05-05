Repositories
============

This section contains documentation for all repository classes that handle database operations and business logic.

.. toctree::
   :maxdepth: 2
   :caption: Repositories

   contacts
   users

Overview
--------

The repository pattern is used to encapsulate data access logic and provide a clean interface for database operations. Each repository handles:

* **Contacts Repository**: Manages CRUD operations for contact records
* **Users Repository**: Handles user authentication, registration, and profile management

These repositories provide a separation between the business logic and the data access layer, making the code more maintainable and testable.
