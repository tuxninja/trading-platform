# Google OAuth Setup Guide

This guide walks you through setting up Google OAuth authentication for the Trading Platform.

## Overview

The Trading Platform uses Google OAuth for user authentication. Users can sign in with their Google accounts to access the trading dashboard and features.

## Prerequisites

- Google Cloud Platform account
- Access to Google Cloud Console
- Administrative access to the Trading Platform repository

## Step 1: Google Cloud Console Setup

### 1.1 Create a New Project (if needed)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: `trading-platform` (or your preferred name)
4. Click "Create"

### 1.2 Enable Google+ API

1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Google+ API"
3. Click on "Google+ API" and click "Enable"

## Step 2: Create OAuth 2.0 Credentials

### 2.1 Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Choose "External" user type (or "Internal" if using Google Workspace)
3. Fill in required information:
   - **App name**: Trading Platform
   - **User support email**: Your email
   - **Developer contact information**: Your email
4. Click "Save and Continue"
5. Skip "Scopes" section for now → "Save and Continue"
6. Add test users if needed → "Save and Continue"

### 2.2 Create OAuth Client ID

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Select "Web application"
4. Enter name: `Trading Platform Web Client`
5. Configure **Authorized JavaScript origins**:
   ```
   http://localhost:3000
   http://divestifi.com
   https://divestifi.com
   ```
6. Configure **Authorized redirect URIs**:
   ```
   http://localhost:3000
   http://divestifi.com
   https://divestifi.com
   ```
7. Click "Create"
8. **Save the Client ID** - you'll need this for configuration

## Step 3: Configure Application

### 3.1 Update Environment Variables

#### For Development (.env.local)
```bash
# Frontend environment
REACT_APP_GOOGLE_CLIENT_ID=your_google_client_id_here.apps.googleusercontent.com
```

#### For Production
1. **GitHub Secrets**: Add `GOOGLE_CLIENT_ID` secret in repository settings
2. **EC2 Environment**: Add to `/opt/trading/.env` file:
   ```bash
   GOOGLE_CLIENT_ID=your_google_client_id_here.apps.googleusercontent.com
   ```

### 3.2 Update Docker Compose

Ensure `docker-compose.prod.yml` includes:
```yaml
frontend:
  environment:
    - REACT_APP_GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:-}
```

### 3.3 Backend CORS Configuration

Verify `backend/config.py` includes your domain in CORS_ORIGINS:
```python
CORS_ORIGINS: list = [
    origin.strip() 
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin.strip()
]
```

## Step 4: Testing Authentication

### 4.1 Development Testing

1. Start the development environment:
   ```bash
   npm start  # Frontend
   python main.py  # Backend
   ```
2. Navigate to `http://localhost:3000`
3. Click "Sign in with Google"
4. Complete OAuth flow
5. Verify redirect to dashboard

### 4.2 Production Testing

1. Navigate to your production URL (e.g., `http://divestifi.com`)
2. Click "Sign in with Google"
3. Complete OAuth flow
4. Verify authentication works correctly

## Troubleshooting

### Common Issues

#### "OAuth client was not found" Error
- **Cause**: Google Client ID not properly configured
- **Solution**: Verify `REACT_APP_GOOGLE_CLIENT_ID` is set correctly
- **Check**: Browser dev tools → Console for specific error

#### "Disallowed CORS origin" Error
- **Cause**: Backend CORS configuration doesn't include your domain
- **Solution**: Add your domain to CORS_ORIGINS environment variable
- **Check**: Network tab for OPTIONS request failures

#### "Missing required parameter: client_id" Error
- **Cause**: Google Client ID not reaching the frontend
- **Solution**: Verify environment variable is set at build time for React
- **Check**: View page source for client ID in JavaScript

#### "Invalid client" Error
- **Cause**: OAuth client not configured for your domain
- **Solution**: Add your domain to Authorized JavaScript origins in Google Cloud Console
- **Note**: IP addresses are not allowed, only domain names

#### Network Error During Login
- **Cause**: Frontend cannot reach backend API
- **Solution**: Check port mappings and CORS configuration
- **Check**: Browser dev tools → Network tab for failed API calls

### Debugging Steps

1. **Check Frontend Environment**:
   ```bash
   # In browser console
   console.log(process.env.REACT_APP_GOOGLE_CLIENT_ID)
   ```

2. **Check Backend CORS**:
   ```bash
   curl -X OPTIONS http://your-domain:8000/api/auth/google \
     -H "Origin: http://your-domain" \
     -H "Access-Control-Request-Method: POST"
   ```

3. **Verify Google Client Configuration**:
   - Go to Google Cloud Console → Credentials
   - Check Authorized JavaScript origins include your domain
   - Ensure domain format is correct (no trailing slashes)

## Security Best Practices

1. **Restrict Domains**: Only add necessary domains to Authorized origins
2. **Use HTTPS**: Configure HTTPS for production (recommended)
3. **Regular Review**: Periodically review OAuth consent screen and credentials
4. **Environment Variables**: Never commit Google Client ID to version control
5. **Least Privilege**: Only request necessary OAuth scopes

## Google Client ID Format

Valid Google Client ID format:
```
123456789012-abcdefghijklmnopqrstuvwxyz123456.apps.googleusercontent.com
```

## Domain Configuration Requirements

- **Development**: `http://localhost:3000`
- **Production**: Use your actual domain name
- **No IP Addresses**: Google OAuth doesn't allow IP addresses
- **Protocol Specific**: Add both HTTP and HTTPS if needed

## Support

If you encounter issues not covered in this guide:

1. Check the [Google OAuth Documentation](https://developers.google.com/identity/oauth2/web/guides/overview)
2. Review the [Troubleshooting Guide](./TROUBLESHOOTING.md)
3. Check browser developer tools for specific error messages
4. Verify all environment variables are properly set

## References

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/oauth2/web)
- [React Google OAuth Library](https://www.npmjs.com/package/@react-oauth/google)
- [Trading Platform API Documentation](../backend/docs/api.md)