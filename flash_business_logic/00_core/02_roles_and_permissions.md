# Roles and Permissions

## Customer
Can:
- Register/login
- Manage profile
- Manage delivery addresses
- Browse available stores/categories/items
- Create orders
- View order details
- Track order status
- View relevant payment/collection details
- Receive notifications
- Cancel only when the current business state permits cancellation

Cannot:
- Assign a driver
- Change store prices
- Change platform fees
- Change order status outside allowed customer transitions

## Driver
Can:
- Login
- View assigned orders
- View order details
- View collection/fee information
- Update allowed delivery statuses
- Complete delivery
- View delivery history

Cannot:
- Accept/reject an assignment manually
- Assign an order to another driver
- Change pricing
- Change platform fees
- Modify store catalog

## Store
Can:
- Login
- Manage store profile
- Manage categories
- Manage products/items
- Receive orders
- Process orders according to allowed transitions
- View driver/order information relevant to operations
- View financial amounts relevant to the store

Cannot:
- Assign drivers manually unless a future admin feature explicitly enables it
- Change platform-wide fee rules
- Modify another store's data

## Admin
Can:
- Manage users
- Manage stores
- Manage drivers
- View/manage orders
- Review assignments
- Manage/configure business settings
- Review financial records
- Review operational reports
- Review audit logs

## Authorization rule
Every API action must validate:
1. authenticated user
2. role
3. object ownership/relationship
4. allowed state transition
5. business constraints
