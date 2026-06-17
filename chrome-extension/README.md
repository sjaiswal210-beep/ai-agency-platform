# WhatsApp Image Reminder - Chrome Extension

A lightweight Chrome extension that shows a floating notification reminding you to attach an image whenever you open WhatsApp Web.

## Features

- Floater notification slides in from the right when WhatsApp Web loads
- Auto-dismisses after 10 seconds (configurable)
- Manual close button
- Shows only once per session to avoid annoyance
- Smooth animations with WhatsApp-themed green gradient

## Installation (Developer Mode)

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right)
3. Click **Load unpacked**
4. Select this `chrome-extension` folder
5. Open [web.whatsapp.com](https://web.whatsapp.com) - the floater will appear!

## Configuration

Edit `content.js` to customize behavior:

```js
const CONFIG = {
  autoHideDelay: 10000,       // ms before auto-hide (0 = never)
  showOncePerSession: true,   // show once per browser session
};
```

## Files

- `manifest.json` - Extension configuration (Manifest V3)
- `content.js` - Logic for detecting WhatsApp load and showing the floater
- `styles.css` - Floater styling and animations
- `icons/` - Extension icons (add your own 48x48 and 128x128 PNGs)
