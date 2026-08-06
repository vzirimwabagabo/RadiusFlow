# RadiusFlow Admin Frontend

This is the frontend administration interface for the RadiusFlow FreeRADIUS management API.

## Features

- User authentication (login/logout)
- Dashboard with system statistics
- User management (create, read, update, delete users)
- Package/Group management (create, read, update, delete packages)
- NAS (Network Access Server) management
- Session monitoring (active and stale sessions)
- Responsive design

## Technology Stack

- React 18
- React Router DOM v7
- Axios for HTTP requests
- Vanilla CSS (custom styling)

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. The application will be available at http://localhost:5173

## Environment Variables

Create a `.env` file in the root directory with:

```
VITE_API_URL=http://localhost:8000/api/v1
```

## API Integration

This frontend communicates with the RadiusFlow backend API running on port 8000. Make sure the backend is running and accessible before using this frontend.

## Components

### Pages
- `Login.js` - Authentication page
- `Dashboard.js` - Overview dashboard with statistics
- `Users.js` - User management interface
- `Packages.js` - Package/group management interface
- `NAS.js` - Network Access Server management
- `Sessions.js` - Session monitoring (active/stale)

### Services
- `api.js` - Axios instance configured with API base URL and auth interceptors

### Contexts
- `AuthContext.js` - React context for managing authentication state

## Usage

1. Start the RadiusFlow backend API (should be running on http://localhost:8000)
2. Start this frontend application
3. Navigate to http://localhost:5173/login
4. Use the demo credentials (username: admin, password: admin) or register a new user through the backend API

## Notes

- This is a demonstration frontend that uses mock authentication. In a production environment, you would implement proper authentication against the backend's `/auth/login` endpoint.
- The UI uses responsive design principles and should work on desktop and mobile devices.
- Error handling is basic and should be enhanced for production use.