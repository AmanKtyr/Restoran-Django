# Kitchen Display System (KDS)

A comprehensive kitchen display system for restaurant order management.

## Features

- Real-time order tracking and management
- Station-based workflow
- Order item status tracking (pending, in progress, ready, delivered, cancelled)
- Kitchen alerts system
- Order history and logs
- Automatic assignment of menu items to kitchen stations
- Dark mode support
- Mobile-responsive design

## Models

- **KitchenStation**: Represents a station in the kitchen (e.g., grill, fry, salad)
- **KitchenDisplay**: Represents a physical display in the kitchen
- **MenuItemStation**: Maps menu items to kitchen stations
- **OrderItemStatus**: Tracks the status of each order item in the kitchen
- **KitchenLog**: Logs events in the kitchen
- **KitchenAlert**: Represents alerts in the kitchen

## Views

- **Dashboard**: Overview of all kitchen activity
- **Station View**: Detailed view for a specific kitchen station
- **Order Detail**: Detailed view of a specific order
- **API Endpoints**: For updating item status, assigning items, creating alerts, etc.

## Usage

1. Set up kitchen stations in the admin panel
2. Assign menu items to stations
3. When orders are placed, they will automatically appear in the kitchen display system
4. Kitchen staff can update the status of items as they are prepared
5. Managers can create alerts for the kitchen staff

## Integration

The Kitchen Display System integrates with:

- Order Management System
- Menu Management System
- User Authentication System
