# Store App Business Logic

## Main areas
- Login
- Store profile
- Categories
- Products/items
- Orders
- Order details
- Operational/financial views

## Catalog
Store can:
- add/edit/deactivate categories
- add/edit/deactivate products
- organize products by category
- manage availability

## Order handling
Store receives orders and processes them through the allowed lifecycle.

Typical flow:
PLACED
-> CONFIRMED
-> PREPARING
-> READY_FOR_PICKUP

After READY_FOR_PICKUP, assignment/delivery is controlled by the platform.

## Store must not
- modify historical order item prices
- directly rewrite financial ledger records
- create invalid order transitions
- bypass backend assignment rules
