# 📍 Where Multi-Device Login Notifications Appear

## 🔔 Notification Locations

Ang notification ay lalabas sa **DALAWANG LUGAR**:

---

## 1️⃣ Notification Bell Dropdown (Navbar)

Makikita sa **lahat ng pages** sa top right corner ng navbar:

```
┌─────────────────────────────────────────────────────────────┐
│  Velare Logo    [Search]    🛒 Cart  🔔 Bell  👤 Profile   │
│                                       ↑                      │
│                                       │                      │
│                              DITO LALABAS!                   │
└─────────────────────────────────────────────────────────────┘
```

### Paano Makikita:

1. **May RED BADGE** sa bell icon kung may unread notification
   ```
   🔔 (3)  ← May 3 unread notifications
   ```

2. **Click ang bell icon** para makita ang dropdown:
   ```
   ┌─────────────────────────────────────────┐
   │ Notifications                           │
   ├─────────────────────────────────────────┤
   │ 🔐 Security                             │
   │ New Device Login Detected               │
   │ Your account was accessed from a new    │
   │ device: Firefox on Windows at           │
   │ February 16, 2026 at 2:30 PM           │
   │ 5m ago                                  │
   ├─────────────────────────────────────────┤
   │ 📦 Order                                │
   │ Order Shipped                           │
   │ Your order #ORD001 is on the way!      │
   │ 1h ago                                  │
   └─────────────────────────────────────────┘
   ```

3. **Click ang notification** para pumunta sa Notifications page

---

## 2️⃣ Notifications Page (Full View)

Makikita sa **My Account → Notifications** page:

### Paano Pumunta:

**Option 1: Click sa bell dropdown**
```
Navbar → 🔔 Bell → Click any notification → Redirects to Notifications page
```

**Option 2: Click sa sidebar**
```
My Account → Notifications tab (sa left sidebar)
```

### Full View:
```
┌─────────────────────────────────────────────────────────────┐
│  My Account                                                  │
├─────────────────────────────────────────────────────────────┤
│  📋 My Profile                                              │
│  📍 My Addresses                                            │
│  🛍️ My Purchases                                            │
│  🔔 Notifications  ← DITO!                                  │
│  🎫 My Vouchers                                             │
│  🔒 Change Password                                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Notifications                    [Mark All as Read]        │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ 🔐 Security                                        │    │
│  │ New Device Login Detected                          │    │
│  │                                                     │    │
│  │ Your account was accessed from a new device:       │    │
│  │ Firefox on Windows at February 16, 2026 at 2:30 PM│    │
│  │                                                     │    │
│  │ If this wasn't you, please change your password   │    │
│  │ immediately.                                        │    │
│  │                                                     │    │
│  │ February 16, 2026 at 2:30 PM                      │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ 📦 Delivery                                        │    │
│  │ Order Shipped                                      │    │
│  │ Your order #ORD001 is now on its way!             │    │
│  │ February 16, 2026 at 1:00 PM                      │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 Notification Appearance

### Security Notification (New Device Login):

```
┌────────────────────────────────────────────────────────┐
│ 🔐 Security                                            │
│ ─────────────────────────────────────────────────────  │
│ New Device Login Detected                              │
│                                                         │
│ Your account was accessed from a new device:           │
│ Firefox on Windows at February 16, 2026 at 2:30 PM    │
│                                                         │
│ If this wasn't you, please change your password       │
│ immediately.                                            │
│                                                         │
│ 📅 February 16, 2026 at 2:30 PM                       │
└────────────────────────────────────────────────────────┘
```

### Features:
- ✅ **Orange/Yellow color** (security warning)
- ✅ **🔐 Icon** (security badge)
- ✅ **Device info** (browser + OS)
- ✅ **Timestamp** (exact time)
- ✅ **Action suggestion** (change password)

---

## 📱 Mobile View

Sa mobile, same lang ang location:

### Navbar (Mobile):
```
┌─────────────────────────────┐
│ ☰  Velare    🛒  🔔  👤    │
│                  ↑          │
│                  │          │
│         DITO LALABAS!       │
└─────────────────────────────┘
```

### Dropdown (Mobile):
```
┌─────────────────────────────┐
│ Notifications               │
├─────────────────────────────┤
│ 🔐 Security                 │
│ New Device Login            │
│ Firefox on Windows          │
│ 5m ago                      │
├─────────────────────────────┤
│ 📦 Order                    │
│ Order Shipped               │
│ 1h ago                      │
└─────────────────────────────┘
```

---

## 🔄 Auto-Refresh

Ang notifications ay **automatically nag-refresh**:

1. **On page load** - Kapag nag-load ng page
2. **Every 30 seconds** - Automatic refresh
3. **After clicking** - After marking as read

Hindi kailangan ng manual refresh!

---

## 🧪 Testing

### Test Scenario:

1. **Login from Chrome**
   ```
   → No notification (first login)
   ```

2. **Login from Firefox** (without logging out from Chrome)
   ```
   → Notification appears!
   → Bell icon shows red badge: 🔔 (1)
   ```

3. **Click bell icon**
   ```
   → Dropdown opens
   → See: "New Device Login Detected"
   → See: "Firefox on Windows"
   ```

4. **Click notification**
   ```
   → Redirects to Notifications page
   → See full details
   → Notification marked as read
   → Badge disappears
   ```

---

## 📊 Notification Flow

```
New Device Login
      ↓
Notification Created in Database
      ↓
Page Loads/Refreshes (automatic every 30s)
      ↓
JavaScript fetches notifications from /api/notifications
      ↓
Bell icon shows red badge (if unread)
      ↓
User clicks bell
      ↓
Dropdown shows notification
      ↓
User clicks notification
      ↓
Redirects to Notifications page
      ↓
Marked as read
```

---

## 🎯 Summary

### Lalabas ang notification sa:

1. **🔔 Bell Icon Dropdown** (top right navbar)
   - Quick preview
   - Shows on all pages
   - Red badge if unread

2. **📄 Notifications Page** (My Account → Notifications)
   - Full details
   - All notifications history
   - Mark as read option

### Paano makikita:

1. Login from different device
2. Wait for page to refresh (or refresh manually)
3. See red badge on bell icon
4. Click bell to see notification
5. Click notification to see full details

---

## 🔧 Technical Details

### API Endpoint:
```
GET /api/notifications
```

### Response:
```json
{
  "success": true,
  "notifications": [
    {
      "notification_id": 1,
      "title": "🔐 New Device Login Detected",
      "message": "Your account was accessed from...",
      "notification_type": "security",
      "is_read": false,
      "created_at": "2026-02-16T14:30:00Z"
    }
  ],
  "unread_count": 1
}
```

### JavaScript File:
```
static/js/notifications.js
```

### Template Files:
```
templates/accounts/myAccount_notification.html  (Full page)
All other templates have the bell dropdown
```

---

**Tapos na! Ang notification ay lalabas automatically sa bell icon at notifications page.** 🎉
