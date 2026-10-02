# Admin Dashboard Business Logic

The dashboard is intentionally simple for MVP but supports advanced operational
views where they provide clear value.

## Core dashboard
Show high-level:
- orders
- active deliveries
- stores
- drivers
- customers
- operational alerts
- financial summaries where approved

## Management areas
### Users
View/search/manage customers, drivers, and relevant accounts.

### Stores
View/store profile, status, categories/products, operational state.

### Drivers
View driver status, active assignments, delivery history and operational
financial information.

### Orders
Search/filter by:
- order ID
- status
- store
- driver
- customer
- date

### Financial
Provide read-only operational summaries initially.
Detailed accounting features can be expanded later.

## Admin principle
Admin actions must be permission-protected and audited.
