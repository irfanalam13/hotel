# PHASE_02_BACKEND_CORE.md

Build the complete Django backend.

Existing apps:

* tenants
* orgs
* accounts
* auditlog
* properties
* rooms
* reservations
* guests
* housekeeping
* maintenance
* inventory
* billing
* pos
* reports
* dashboards
* integrations
* channels
* support
* exports
* contracts
* ai_assistant

Requirements:

## Authentication

Implement:

* Custom User Model
* JWT Authentication
* Refresh Tokens
* RBAC Permissions

Roles:

* Super Admin
* Organization Admin
* Property Manager
* Receptionist
* Housekeeping Staff
* Maintenance Staff
* Accountant
* Guest

## Reservations

Implement:

* Availability Search
* Booking Creation
* Booking Modification
* Booking Cancellation
* Check-In
* Check-Out

Prevent double bookings using database transactions.

## Database

Use PostgreSQL.

Requirements:

* UUID primary keys
* Soft Deletes
* Created/Updated timestamps
* Database indexes
* Constraints

Create serializers, APIs, permissions, tests, and Swagger documentation.

Code must be production ready.
