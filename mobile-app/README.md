# City Maps Business - Mobile App

Android app for business owners to access their City Maps dashboard.

## Features
- Phone OTP login (no password needed)
- Dashboard with all enabled modules
- CRM - view/call/WhatsApp contacts
- Push notifications for new leads, bookings, payments
- Profile & plan management

## Tech Stack
- Expo / React Native
- TypeScript
- React Navigation (bottom tabs)
- Expo Secure Store (auth tokens)
- Expo Notifications (push)

## Setup

```bash
cd mobile-app
npm install
npx expo start
```

Scan the QR code with Expo Go app on your phone.

## Build APK

```bash
npx eas build --platform android --profile preview
```

## Backend API
The app uses these endpoints:
- POST /api/mobile-auth/send-otp
- POST /api/mobile-auth/verify-otp
- GET /api/organizations/{id}/modules
- GET /api/org/{id}/crm/contacts

## Project Structure
```
mobile-app/
  App.tsx              <- Entry point
  src/
    screens/
      LoginScreen.tsx      <- OTP login
      DashboardScreen.tsx  <- Module grid
      CRMScreen.tsx        <- Contacts + call/WhatsApp
      NotificationsScreen.tsx
      ProfileScreen.tsx
    lib/
      api.ts           <- API calls
      storage.ts       <- Secure token storage
  app.json             <- Expo config
  package.json
```

## Next Steps
- [ ] Push notifications (FCM)
- [ ] Booking screen
- [ ] Invoice generation
- [ ] QR code scanner for walk-ins
- [ ] Voice notes for CRM activities
- [ ] Offline mode