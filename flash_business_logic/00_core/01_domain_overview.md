# Flash Domain Overview

## Main actors

### Customer
Creates delivery orders, provides delivery information, tracks orders,
and handles the customer-side payment/collection flow.

### Store
Represents a business such as:
- Pharmacy
- Supermarket
- Flower shop
- Restaurant
- Other retail/service businesses

A store can create and manage multiple categories and products/items.

### Driver
Executes delivery orders assigned by the platform.
The driver does not choose whether to accept or reject an assigned order.

The driver may:
- See assigned orders
- See store/customer information needed for delivery
- See amounts to collect from the customer
- See fees/amounts payable to the store according to the platform rules
- Update delivery progress
- Complete delivery

### Admin
Operates the platform, manages users/stores/drivers/orders and monitors
financial and operational activity.

## Core entities

- User
- Customer Profile
- Driver Profile
- Store
- Store Category
- Product / Item
- Address
- Order
- Order Item
- Order Status History
- Driver Assignment
- Payment / Collection
- Store Fee / Driver Fee
- Wallet / Ledger Entry
- Notification
- Admin Action / Audit Log
