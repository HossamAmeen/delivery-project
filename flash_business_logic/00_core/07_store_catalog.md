# Store and Catalog Logic

## Store
A store can represent many business types, including pharmacy,
supermarket, flower shop, and other supported businesses.

## Categories
A store can create multiple categories.

Category fields should conceptually include:
- name
- description (optional)
- image (optional)
- active/inactive
- sort order

## Products/items
Products belong to a store category and store.

Conceptual fields:
- name
- description
- price
- image
- category
- active/inactive
- availability
- sort order

## Historical orders
Order items must store snapshots of relevant product data.
Changing a product later must not alter an existing order.

## Catalog visibility
Only active/available products should be orderable.
The backend validates availability even if the UI currently displays an item.
