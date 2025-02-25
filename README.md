# Events Microservice

This microservice is built using **FastAPI**, **Strawberry (GraphQL)**, and **MongoDB**. It serves as a subgraph handling **event-related data and operations**, providing queries and mutations to manage events, reminders, finances, and reports.

## Features

- **GraphQL API**: Implements queries and mutations for event management.
- **Event Operations**: Supports creating, updating, and retrieving events.
- **Reminders & Notifications**: Handles automated reminders via emails.
- **Financial Management**: Tracks and manages event-related finances.
- **Reports & Holidays**: Supports event reports and holiday scheduling.
- **Database Integration**: Uses MongoDB for storage.

## Usage

This is a microservice and the full docker setup can be found in the [`services`](https://github.com/Clubs-Council-IIITH/services) repo. To use it
please visit `setup` repo

1. Go to [Clubs-Council-IIITH Services Repository](https://github.com/Clubs-Council-IIITH/setup).
2. Follow the setup instructions provided there.

## Developer Info

- **GraphQL Endpoint**: `http://events/graphql` (Accessible via the gateway)

### Available GraphQL Operations:

#### Queries
- Retrieve event details, finances, reports, and holidays.

#### Mutations
- Create, update, and manage events, reminders, finances, and reports.
