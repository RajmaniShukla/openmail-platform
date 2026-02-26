# 📖 OpenMail Platform - User Manual

**Version:** 1.0  
**Last Updated:** 2026-02-26  
**Platform:** OpenMail v1.0.0

---

## 📋 Table of Contents

1. [Introduction](#1-introduction)
2. [Getting Started](#2-getting-started)
3. [User Registration & Login](#3-user-registration--login)
4. [Dashboard Overview](#4-dashboard-overview)
5. [Reading Emails](#5-reading-emails)
6. [Composing & Sending Emails](#6-composing--sending-emails)
7. [Email Organization](#7-email-organization)
8. [Search Functionality](#8-search-functionality)
9. [Contacts Management](#9-contacts-management)
10. [Domain Management](#10-domain-management)
11. [Email Filters & Rules](#11-email-filters--rules)
12. [Settings & Preferences](#12-settings--preferences)
13. [Keyboard Shortcuts](#13-keyboard-shortcuts)
14. [Mobile Usage](#14-mobile-usage)
15. [Troubleshooting](#15-troubleshooting)
16. [FAQ](#16-faq)

---

## 1. Introduction

### What is OpenMail?

OpenMail is a **professional-grade, self-hosted email platform** that provides all the features you expect from modern email services like Gmail or Outlook, while giving you complete control over your data.

### Key Features

- ✉️ **Full Email Support** - Send, receive, reply, forward
- 📁 **Smart Organization** - Folders, labels, filters
- 🔍 **Powerful Search** - Full-text search across all emails
- 📎 **Attachments** - Up to 25MB per email
- 🏷️ **Labels & Tags** - Flexible categorization
- 🌐 **Custom Domains** - Use your own email domain
- 🔒 **Security** - DKIM, SPF, spam filtering
- 📱 **Responsive** - Works on desktop & mobile

### System Requirements

**For Web Access:**
- Modern web browser (Chrome, Firefox, Safari, Edge)
- JavaScript enabled
- Internet connection

**For Email Clients (IMAP/SMTP):**
- Any standard email client
- IMAP/SMTP support

---

## 2. Getting Started

### Accessing OpenMail

1. Open your web browser
2. Navigate to your OpenMail URL (e.g., `https://mail.yourdomain.com`)
3. You'll see the login page

### First-Time Setup

If you're a new user:
1. Click **"Create Account"** on the login page
2. Fill in your details
3. Verify your email address
4. Complete your profile setup

---

## 3. User Registration & Login

### Creating a New Account

1. Click **"Create Account"** or **"Register"**
2. Fill in the required information:
   - **Email Address**: Your desired email (e.g., john@yourdomain.com)
   - **Password**: Minimum 8 characters, include numbers and special characters
   - **First Name**: Your first name
   - **Last Name**: Your last name
3. Accept the Terms of Service
4. Click **"Create Account"**
5. Check your email for a verification link
6. Click the verification link to activate your account

### Logging In

1. Enter your **email address**
2. Enter your **password**
3. (Optional) Check **"Remember me"** to stay logged in
4. Click **"Sign In"**

### Forgot Password

1. Click **"Forgot Password?"** on the login page
2. Enter your email address
3. Click **"Send Reset Link"**
4. Check your email for the reset link
5. Click the link and enter your new password
6. Log in with your new password

### Account Security

- **Password Requirements:**
  - Minimum 8 characters
  - Mix of uppercase and lowercase
  - At least one number
  - At least one special character

- **Security Tips:**
  - Don't share your password
  - Log out on shared computers
  - Change password regularly
  - Watch for suspicious activity

---

## 4. Dashboard Overview

### Main Interface Layout

```
┌─────────────────────────────────────────────────────────────┐
│  🔍 Search                              👤 Profile  ⚙️     │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│  📥 Inbox    │     EMAIL LIST                              │
│  ⭐ Starred  │  ┌─────────────────────────────────────────┐│
│  📤 Sent     │  │ ☐ From: John       Subject: Meeting... ││
│  📝 Drafts   │  │ ☐ From: Sarah      Subject: Report...  ││
│  🗑️ Trash    │  │ ☐ From: System     Subject: Welcome... ││
│  📦 Archive  │  └─────────────────────────────────────────┘│
│  🚫 Spam     │                                              │
│              │                                              │
│  ─────────── │                                              │
│  Labels      │                                              │
│  🔴 Work     │                                              │
│  🔵 Personal │                                              │
│  🟢 Finance  │                                              │
│              │                                              │
│  [+ New]     │                                              │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

### Navigation Elements

| Element | Location | Function |
|---------|----------|----------|
| Search Bar | Top | Search all emails |
| Compose Button | Top-left | Create new email |
| Folder List | Left sidebar | Navigate folders |
| Label List | Left sidebar (bottom) | Filter by label |
| Email List | Center | View emails in folder |
| Profile Menu | Top-right | Account settings |
| Settings Icon | Top-right | App settings |

### Folder Icons

| Icon | Folder | Description |
|------|--------|-------------|
| 📥 | Inbox | Incoming emails |
| ⭐ | Starred | Important emails |
| 📤 | Sent | Sent emails |
| 📝 | Drafts | Unsent drafts |
| 🗑️ | Trash | Deleted emails |
| 📦 | Archive | Archived emails |
| 🚫 | Spam | Spam/junk |

---

## 5. Reading Emails

### Viewing an Email

1. Click on any email in the list
2. The email opens in the reading pane
3. Email is automatically marked as read

### Email View Components

```
┌─────────────────────────────────────────────────────────────┐
│ Subject: Quarterly Report Q4 2025                           │
├─────────────────────────────────────────────────────────────┤
│ From: Sarah Johnson <sarah@company.com>                     │
│ To: you@yourdomain.com                                      │
│ Date: Feb 26, 2026, 10:30 AM                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Hi,                                                         │
│                                                             │
│ Please find attached the quarterly report...                │
│                                                             │
│ Best regards,                                               │
│ Sarah                                                       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ 📎 Attachments:                                             │
│ ├── Q4_Report.pdf (2.3 MB)      [Download] [Preview]       │
│ └── Charts.xlsx (450 KB)        [Download]                 │
├─────────────────────────────────────────────────────────────┤
│ [Reply] [Reply All] [Forward] [⭐ Star] [🗑️ Delete] [More ▼]│
└─────────────────────────────────────────────────────────────┘
```

### Email Actions

| Action | Description | Shortcut |
|--------|-------------|----------|
| Reply | Reply to sender | `R` |
| Reply All | Reply to all recipients | `A` |
| Forward | Forward to others | `F` |
| Star | Mark as important | `S` |
| Delete | Move to trash | `Delete` |
| Archive | Move to archive | `E` |
| Mark Unread | Mark as unread | `U` |
| Move to | Move to folder | `V` |
| Label | Add/remove labels | `L` |

### Handling Attachments

**Downloading:**
1. Click the **Download** button next to the attachment
2. File saves to your downloads folder

**Previewing:**
1. Click **Preview** for supported file types
2. PDF, images, and documents can be previewed
3. Press `Esc` to close preview

**Saving All:**
1. Click **"Download All"** to save all attachments as a ZIP

---

## 6. Composing & Sending Emails

### Creating a New Email

1. Click the **"Compose"** button (or press `C`)
2. The compose window opens

### Compose Window

```
┌─────────────────────────────────────────────────────────────┐
│ New Message                                    [─] [□] [×] │
├─────────────────────────────────────────────────────────────┤
│ To:      [recipient@example.com                          ] │
│ Cc:      [                                               ] │
│ Bcc:     [                                               ] │
│ Subject: [                                               ] │
├─────────────────────────────────────────────────────────────┤
│ [B] [I] [U] [🔗] [📷] [≡] [—]                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Type your message here...                                   │
│                                                             │
│                                                             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ 📎 Attachments: (none)                                     │
├─────────────────────────────────────────────────────────────┤
│ [📎 Attach] [🗑️ Discard]                         [Send ➤] │
└─────────────────────────────────────────────────────────────┘
```

### Adding Recipients

**To Field:**
- Type email addresses
- Press `Enter` or `Tab` to add multiple
- Start typing a name to see suggestions from contacts

**Cc (Carbon Copy):**
- Recipients can see who else received the email
- Click "Cc" to expand the field

**Bcc (Blind Carbon Copy):**
- Recipients cannot see other Bcc addresses
- Click "Bcc" to expand the field

### Formatting Text

| Button | Function | Shortcut |
|--------|----------|----------|
| **B** | Bold | `Ctrl+B` |
| *I* | Italic | `Ctrl+I` |
| U̲ | Underline | `Ctrl+U` |
| 🔗 | Insert link | `Ctrl+K` |
| 📷 | Insert image | - |
| ≡ | Bullet list | - |
| — | Numbered list | - |

### Adding Attachments

1. Click the **📎 Attach** button
2. Select files from your computer
3. Or drag and drop files onto the compose window
4. Files appear in the attachments section

**Attachment Limits:**
- Maximum file size: 25 MB per file
- Maximum total: 25 MB per email
- Supported types: Documents, images, archives

### Sending the Email

1. Fill in recipients, subject, and message
2. Add any attachments
3. Click **"Send"** (or press `Ctrl+Enter`)
4. Email is sent and saved to "Sent" folder

### Saving as Draft

- Drafts are automatically saved while composing
- Click **"Save Draft"** to manually save
- Access drafts from the **Drafts** folder
- Resume composing by opening the draft

### Discarding an Email

1. Click **"🗑️ Discard"**
2. Confirm deletion
3. Draft is permanently deleted

---

## 7. Email Organization

### Using Folders

**Default Folders:**
- **Inbox** - New incoming emails
- **Sent** - Emails you've sent
- **Drafts** - Unsent emails
- **Starred** - Important/favorited emails
- **Trash** - Deleted emails (auto-cleared after 30 days)
- **Spam** - Suspected spam (auto-cleared after 30 days)
- **Archive** - Archived emails

**Creating Custom Folders:**
1. Click **"+ New Folder"** in the sidebar
2. Enter folder name
3. Choose parent folder (optional)
4. Select color/icon (optional)
5. Click **"Create"**

**Moving Emails to Folders:**
1. Select email(s) using checkboxes
2. Click **"Move to"** or press `V`
3. Select destination folder
4. Or drag and drop emails to folders

### Using Labels

Labels allow emails to have multiple categories.

**Creating Labels:**
1. Click **"+ New Label"** in the sidebar
2. Enter label name
3. Choose color
4. Click **"Create"**

**Applying Labels:**
1. Open an email or select multiple
2. Click the **Label** icon or press `L`
3. Check/uncheck labels to apply
4. Labels appear as colored tags on emails

**Filtering by Label:**
- Click a label in the sidebar to show all emails with that label

### Starring Emails

Mark important emails with a star:
1. Click the ⭐ icon next to any email
2. Or press `S` when viewing an email
3. View all starred emails in the **Starred** folder

### Archiving Emails

Remove emails from inbox without deleting:
1. Select email(s)
2. Click **Archive** or press `E`
3. Email moves to **Archive** folder
4. Find archived emails by searching or in Archive folder

### Deleting Emails

**Move to Trash:**
1. Select email(s)
2. Click **Delete** or press `Delete`
3. Email moves to Trash

**Empty Trash:**
1. Go to **Trash** folder
2. Click **"Empty Trash"**
3. Confirm permanent deletion

**Restore from Trash:**
1. Open Trash folder
2. Select email(s)
3. Click **"Move to"** and select destination

---

## 8. Search Functionality

### Basic Search

1. Click the search bar (or press `/`)
2. Type your search terms
3. Press `Enter`
4. Results appear in the email list

### Search Operators

| Operator | Example | Description |
|----------|---------|-------------|
| from: | from:john@example.com | Emails from specific sender |
| to: | to:jane@example.com | Emails sent to recipient |
| subject: | subject:meeting | Search in subject line |
| has:attachment | has:attachment | Emails with attachments |
| is:starred | is:starred | Starred emails only |
| is:unread | is:unread | Unread emails |
| is:read | is:read | Read emails |
| in:inbox | in:inbox | In specific folder |
| label:work | label:work | Has specific label |
| before: | before:2026-01-01 | Before date |
| after: | after:2026-01-01 | After date |
| larger: | larger:5MB | Larger than size |
| smaller: | smaller:1MB | Smaller than size |

### Combined Searches

Combine operators for precise searches:

```
from:boss@company.com subject:urgent after:2026-01-01 has:attachment
```

This finds emails from your boss with "urgent" in the subject, after Jan 1, with attachments.

### Saving Searches

1. Perform a search
2. Click **"Save Search"**
3. Enter a name
4. Saved search appears in sidebar

---

## 9. Contacts Management

### Accessing Contacts

1. Click **"Contacts"** in the navigation
2. Or press `G` then `C`

### Contact List View

```
┌─────────────────────────────────────────────────────────────┐
│ Contacts                              [+ Add Contact]       │
├─────────────┬───────────────────────────────────────────────┤
│ All         │ Name           Email              Phone       │
│ Frequent    │ ─────────────────────────────────────────────│
│ ─────────── │ John Smith     john@example.com   +1-555-123 │
│ 👥 Groups   │ Sarah Jones    sarah@work.com     +1-555-456 │
│   Work      │ Mike Brown     mike@company.com   +1-555-789 │
│   Personal  │                                              │
│   Family    │                                              │
└─────────────┴───────────────────────────────────────────────┘
```

### Adding a Contact

1. Click **"+ Add Contact"**
2. Fill in contact details:
   - Name (First, Last)
   - Email address(es)
   - Phone number(s)
   - Company
   - Notes
3. Click **"Save"**

### Editing a Contact

1. Click on a contact
2. Click **"Edit"**
3. Modify information
4. Click **"Save"**

### Creating Contact Groups

1. Click **"+ New Group"**
2. Enter group name
3. Add contacts to group
4. Use groups for easy emailing

### Importing Contacts

1. Click **"Import"**
2. Select file format (CSV, vCard)
3. Upload your contact file
4. Map fields if needed
5. Click **"Import"**

### Exporting Contacts

1. Select contacts (or all)
2. Click **"Export"**
3. Choose format (CSV, vCard)
4. Download the file

---

## 10. Domain Management

### Why Custom Domains?

Use your own domain (e.g., you@yourcompany.com) instead of the default domain.

### Adding a Domain

1. Go to **Settings** → **Domains**
2. Click **"+ Add Domain"**
3. Enter your domain name (e.g., yourcompany.com)
4. Click **"Add"**

### Verifying a Domain

After adding, you must verify ownership:

1. View the verification instructions
2. Add the required DNS records:
   - **TXT Record** for verification
   - **MX Record** for email routing
   - **SPF Record** for sender authentication
   - **DKIM Record** for email signing
3. Wait for DNS propagation (up to 48 hours)
4. Click **"Verify Domain"**

### DNS Records Example

```
# MX Record (email routing)
yourcompany.com.  MX  10  mail.openmail.example.com.

# SPF Record (sender policy)
yourcompany.com.  TXT  "v=spf1 include:openmail.example.com ~all"

# DKIM Record (email signing)
mail._domainkey.yourcompany.com.  TXT  "v=DKIM1; k=rsa; p=MIIBIj..."

# DMARC Record (authentication policy)
_dmarc.yourcompany.com.  TXT  "v=DMARC1; p=quarantine; rua=mailto:dmarc@yourcompany.com"
```

### Creating Mailboxes

After domain verification:

1. Go to **Settings** → **Mailboxes**
2. Click **"+ New Mailbox"**
3. Enter the local part (e.g., "sales" for sales@yourcompany.com)
4. Select the domain
5. Set quota (storage limit)
6. Click **"Create"**

---

## 11. Email Filters & Rules

### What Are Filters?

Filters automatically organize incoming emails based on rules you define.

### Creating a Filter

1. Go to **Settings** → **Filters**
2. Click **"+ Create Filter"**
3. Define conditions:
   - From contains: [email/domain]
   - To contains: [email]
   - Subject contains: [text]
   - Has attachment: [yes/no]
4. Define actions:
   - Move to folder
   - Apply label
   - Mark as read
   - Star the message
   - Delete
   - Forward to
5. Click **"Save Filter"**

### Filter Examples

**Example 1: Auto-label newsletters**
```
Condition: From contains "newsletter@"
Action: Apply label "Newsletters"
```

**Example 2: Important work emails**
```
Condition: From contains "@company.com" AND Subject contains "urgent"
Action: Star, Apply label "Urgent"
```

**Example 3: Auto-archive notifications**
```
Condition: From contains "noreply@"
Action: Mark as read, Move to Archive
```

### Managing Filters

- **Edit**: Click filter name → Edit → Save
- **Disable**: Toggle the switch to disable temporarily
- **Delete**: Click delete icon → Confirm
- **Reorder**: Drag filters to change priority

---

## 12. Settings & Preferences

### Accessing Settings

1. Click the ⚙️ gear icon (top-right)
2. Or press `G` then `S`

### General Settings

| Setting | Options | Description |
|---------|---------|-------------|
| Language | English, Spanish, etc. | Interface language |
| Time Zone | Auto / Manual | Time display |
| Date Format | MM/DD/YYYY, DD/MM/YYYY | Date display format |
| Theme | Light / Dark / Auto | Color scheme |

### Email Settings

| Setting | Description |
|---------|-------------|
| Signature | Add signature to outgoing emails |
| Reply Position | Top or bottom of quoted text |
| Default Reply | Reply / Reply All |
| Send Cancellation | Seconds to undo send |
| Read Receipts | Request read confirmations |

### Creating a Signature

1. Go to **Settings** → **Signature**
2. Enable signature
3. Create your signature using the editor:
   ```
   Best regards,
   John Smith
   Senior Developer
   yourcompany.com
   +1-555-123-4567
   ```
4. Choose when to include (all emails, replies, new only)
5. Click **"Save"**

### Notification Settings

| Setting | Description |
|---------|-------------|
| Desktop Notifications | Browser notifications for new mail |
| Sound | Play sound on new mail |
| Email Digest | Daily summary email |

### Vacation Responder

1. Go to **Settings** → **Vacation Responder**
2. Enable auto-reply
3. Set date range
4. Write your message:
   ```
   Thank you for your email. I'm currently out of office
   and will respond when I return on [date].
   
   For urgent matters, please contact [colleague].
   ```
5. Click **"Save"**

---

## 13. Keyboard Shortcuts

### Global Shortcuts

| Shortcut | Action |
|----------|--------|
| `C` | Compose new email |
| `/` | Focus search |
| `?` | Show keyboard shortcuts |
| `Esc` | Close dialog/deselect |

### Navigation

| Shortcut | Action |
|----------|--------|
| `G` then `I` | Go to Inbox |
| `G` then `S` | Go to Starred |
| `G` then `T` | Go to Sent |
| `G` then `D` | Go to Drafts |
| `G` then `A` | Go to Archive |
| `G` then `C` | Go to Contacts |
| `J` | Next email |
| `K` | Previous email |

### Email Actions

| Shortcut | Action |
|----------|--------|
| `Enter` | Open email |
| `R` | Reply |
| `A` | Reply All |
| `F` | Forward |
| `S` | Star/unstar |
| `E` | Archive |
| `#` or `Delete` | Delete |
| `U` | Mark unread |
| `L` | Open labels |
| `V` | Move to folder |

### Selection

| Shortcut | Action |
|----------|--------|
| `X` | Select/deselect email |
| `*` then `A` | Select all |
| `*` then `N` | Deselect all |
| `*` then `R` | Select read |
| `*` then `U` | Select unread |

### Compose Window

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Send email |
| `Ctrl+S` | Save draft |
| `Ctrl+B` | Bold |
| `Ctrl+I` | Italic |
| `Ctrl+U` | Underline |
| `Ctrl+K` | Insert link |

---

## 14. Mobile Usage

### Responsive Design

OpenMail is fully responsive and works on all devices:
- Smartphones
- Tablets
- Desktop computers

### Mobile Interface

On smaller screens:
- Sidebar becomes a hamburger menu
- Swipe gestures for actions
- Optimized touch targets

### Mobile-Specific Features

| Gesture | Action |
|---------|--------|
| Swipe left | Delete email |
| Swipe right | Archive email |
| Pull down | Refresh inbox |
| Long press | Select multiple |

### Mobile Tips

1. **Add to Home Screen** - Install as a PWA for app-like experience
2. **Enable Notifications** - Get push notifications for new mail
3. **Use Landscape** - Rotate for better compose experience

---

## 15. Troubleshooting

### Cannot Log In

1. **Check credentials** - Ensure email and password are correct
2. **Clear cache** - Clear browser cache and cookies
3. **Try incognito** - Test in private/incognito mode
4. **Reset password** - Use "Forgot Password" link
5. **Check caps lock** - Passwords are case-sensitive

### Emails Not Sending

1. **Check connection** - Ensure internet connectivity
2. **Check recipient** - Verify email address is valid
3. **Check attachments** - Ensure under 25MB limit
4. **Check sent folder** - Email may have sent successfully
5. **Try later** - Temporary server issues

### Not Receiving Emails

1. **Check spam folder** - Email may be marked as spam
2. **Check filters** - Filter may be moving emails
3. **Wait** - Email delivery can take a few minutes
4. **Verify domain** - Ensure MX records are correct
5. **Contact sender** - Ask them to resend

### Slow Performance

1. **Clear cache** - Browser cache may be full
2. **Reduce emails per page** - Lower in settings
3. **Close tabs** - Too many tabs slow browser
4. **Try different browser** - Chrome/Firefox recommended
5. **Check connection** - Test internet speed

### Attachments Not Working

1. **Check file size** - Must be under 25MB
2. **Check file type** - Some types may be blocked
3. **Try different file** - Original may be corrupted
4. **Clear cache** - Try after clearing browser cache
5. **Compress file** - ZIP large files

---

## 16. FAQ

### Account & Security

**Q: How do I change my password?**
A: Settings → Security → Change Password

**Q: Can I use two-factor authentication?**
A: Yes, enable in Settings → Security → 2FA (if available)

**Q: How do I delete my account?**
A: Contact your administrator for account deletion

### Email

**Q: What's the maximum attachment size?**
A: 25MB per email

**Q: Can I recall a sent email?**
A: No, but you have a few seconds to "Undo Send" after clicking send

**Q: How long are deleted emails kept?**
A: 30 days in Trash before permanent deletion

**Q: Can I schedule emails to send later?**
A: Yes, click the arrow next to Send → Schedule Send

### Domains

**Q: Can I use multiple domains?**
A: Yes, add multiple domains in Settings → Domains

**Q: How long does domain verification take?**
A: DNS changes can take up to 48 hours to propagate

### Storage

**Q: What's my storage limit?**
A: Default is 5GB, check Settings → Storage

**Q: How do I free up storage?**
A: Delete old emails, empty trash, remove large attachments

---

## 📞 Support

If you need additional help:

- **Documentation**: Check our full documentation
- **Admin Contact**: Contact your system administrator
- **Community**: Join our community forums

---

*OpenMail Platform User Manual v1.0*
*Generated by Chanakya 🧠*
