# Authentication System Setup

## Overview
The AI Learning Map now includes a complete authentication system using PocketBase for user management and modern shadcn/ui-inspired design.

## Features

### 🔐 Authentication
- **User Registration**: Clean signup form with password strength validation
- **User Login**: Secure login with email/password authentication
- **Session Management**: Token-based authentication with cookies
- **Logout**: Secure logout with session cleanup

### 🎨 Modern UI Design
- **shadcn/ui Inspired**: Clean, modern interface with smooth animations
- **Responsive Design**: Works perfectly on desktop and mobile
- **Visual Feedback**: Loading states, error handling, and success messages
- **Gradient Backgrounds**: Beautiful gradient backgrounds for auth pages

### 🛡️ Security Features
- **Password Validation**: Strong password requirements with visual feedback
- **Input Validation**: Client and server-side validation
- **Secure Cookies**: HTTP-only cookies for token storage
- **Error Handling**: Graceful error handling with user-friendly messages

## API Endpoints

### Authentication Routes
- `GET /login` - Login page
- `GET /signup` - Signup page
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User authentication
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user info

### Request/Response Examples

#### Signup Request
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "passwordConfirm": "SecurePassword123!"
}
```

#### Login Request
```json
{
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

#### Success Response
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": "user_id",
    "email": "john@example.com",
    "name": "John Doe"
  },
  "token": "jwt_token_here"
}
```

## File Structure

```
templates/
├── auth/
│   ├── login.html          # Login page template
│   └── signup.html         # Signup page template
├── partials_navigation.html # User navigation component
└── base.html               # Updated base template

app.py                      # Updated with auth routes and middleware
```

## Setup Instructions

1. **PocketBase Configuration**
   - Ensure PocketBase is running with user collection
   - Set environment variables:
     - `POCKETBASE_URL`
     - `POCKETBASE_EMAIL`
     - `POCKETBASE_PASSWORD`

2. **Database Schema**
   - PocketBase will automatically create the `users` collection
   - Required fields: `email`, `password`, `passwordConfirm`, `name`

3. **Run the Application**
   ```bash
   python run_server.py
   ```

## User Experience

### For New Users
1. Visit the main page `/`
2. Click "Sign Up" in the top-right corner
3. Fill out the registration form with strong password
4. Get redirected to login page after successful registration
5. Login with credentials
6. Access the main learning map with personalized experience

### For Existing Users
1. Visit the main page `/`
2. Click "Login" in the top-right corner
3. Enter email and password
4. Access the main learning map with personalized experience

### Navigation
- **Authenticated users**: See welcome message with name and logout button
- **Unauthenticated users**: See login and signup buttons
- **All users**: Can access the main learning map functionality

## Security Notes

- Tokens are stored in secure HTTP-only cookies
- Passwords are validated for strength (8+ chars, mixed case, numbers, symbols)
- All authentication requests include proper error handling
- Session management is handled by PocketBase's built-in security features

## Customization

The UI is built with modern CSS and can be easily customized:
- Colors and gradients in the CSS variables
- Form styling in the auth templates
- Navigation styling in the partials_navigation.html

The design follows shadcn/ui principles with:
- Clean, minimal interface
- Smooth animations and transitions
- Proper spacing and typography
- Responsive design patterns
