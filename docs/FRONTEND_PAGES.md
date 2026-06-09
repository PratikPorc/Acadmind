# AcadMind Frontend — Page & Screen Reference

> **Purpose:** This document describes every screen, layout, and interaction in the AcadMind frontend. Use it as a brief for **Stitch** (or any design tool) to redesign the UI while preserving functionality and user flows.

---

## Product overview

**AcadMind** is an AI-powered campus platform for **Techno India University**. It has two separate portals:

| Portal | Route | Brand name | Primary user |
|--------|-------|------------|--------------|
| Faculty | `/faculty` | **Campus Manager** | Teachers / faculty |
| Student | `/student` | **DigiCampus** | Students |

Both portals share the same dark theme and design language but use different accent colors (violet vs sky blue).

**Core features:**
- Faculty creates batches, subjects, and campus announcements (notices, exams, assignments, file uploads)
- Faculty adds students to batches by **12-digit institutional Student ID**
- Students see a campus feed, enrolled batches, and an AI assistant that answers questions from batch data
- Jarvis (student only) — screenshot upload for future OCR/event extraction (currently stub)

**Important:** There is **no “Switch portal” button** in headers. Users enter via the landing page (`/`) and pick Faculty or Student.

---

## Tech stack (constraints for redesign)

| Layer | Choice |
|-------|--------|
| Framework | React 19 + TypeScript |
| Build | Vite |
| Styling | Tailwind CSS v4 |
| Routing | React Router v7 |
| Auth | Supabase (separate session per portal tab) |
| API | REST via `/api/v1/faculty/*` and `/api/v1/student/*` |

Design deliverables should map to **React components** and remain **mobile-responsive**. Max content width on authenticated pages: **~1152px (`max-w-6xl`)**.

---

## Design system (current)

### Theme
- **Mode:** Dark only
- **Page background:** `#08080d`
- **Surface / cards:** `#12121a` → `#1a1a26` with `border-zinc-800`
- **Primary text:** `#e4e4e7` (zinc-100)
- **Muted text:** `#71717a` (zinc-500/600)
- **Font:** Inter, system-ui

### Accent colors
| Token | Hex / Tailwind | Usage |
|-------|----------------|-------|
| Faculty accent | `#a78bfa` / violet-400 | Faculty labels, batch codes, links |
| Student accent | `#38bdf8` / sky-400 | Student labels, batch codes |
| Primary action | `#6366f1` / indigo-600 | Buttons, active tabs |
| Success | `#34d399` / emerald-400 | Success messages, ok status |
| Warning | `#fbbf24` / amber-400 | Due dates, profile errors |
| Error | red-400 | Form/API errors |

### Reusable patterns
- **Card:** Rounded 2xl, border `zinc-800`, bg `zinc-900/80`, optional backdrop blur
- **Input (`.input-dark`):** Rounded xl, border `zinc-700`, bg `zinc-800/80`, focus border indigo-500
- **Pill badges:** Rounded-full, semi-transparent colored backgrounds by type (exam, assignment, notice, resource)
- **Sticky header:** `zinc-900/90` + backdrop blur, bottom border `zinc-800`

### Feed item type colors
| Type | Badge color |
|------|-------------|
| exam | Red |
| assignment | Amber |
| resource | Emerald |
| notice | Sky |
| default | Indigo |

---

## Route map

```
/                    → Landing Page (portal picker)
/faculty             → Faculty Auth OR Faculty Dashboard
/faculty/*           → Same (no nested routes yet; state-driven views)
/student             → Student Auth OR Student Dashboard
/student/*           → Same (tab-based views)
*                    → Redirect to /
```

Authenticated views are **not separate URLs** — they are gated by Supabase session and in-app state (batch detail, tabs).

---

## Screen 1 — Landing Page

**Route:** `/`  
**File:** `frontend/src/pages/LandingPage.tsx`  
**Auth:** None

### Purpose
Entry point. User chooses Faculty or Student portal.

### Layout
- Full viewport, centered content
- Institution label: “Techno India University”
- Hero title: **AcadMind** (gradient indigo → violet)
- Subtitle: “AI-powered campus platform — notices, deadlines, resources & intelligent Q&A”

### Main content
Two large clickable cards (2-column grid on sm+):

| Card | Link | Title | Subtitle | Accent |
|------|------|-------|----------|--------|
| Faculty | `/faculty` | Campus Manager | Batches · subjects · announcements · resources | Violet hover glow |
| Student | `/student` | DigiCampus | Feed · deadlines · AI assistant · Jarvis | Sky hover glow |

### Footer note
“Open both portals in separate tabs to test faculty & student in parallel”

### States
- Static only (no loading/error)

---

## Screen 2 — Auth (Sign in / Sign up)

**Route:** `/faculty` or `/student` (when not logged in)  
**File:** `frontend/src/components/AuthPage.tsx`  
**Auth:** Supabase email/password; signup via backend auto-confirm (no email verification step)

### Purpose
Login or register. Same component, different copy and fields based on portal.

### Layout
- Full viewport centered card (`max-w-md`)
- Portal label: “Faculty Portal” (violet) or “Student Portal” (sky)
- Title toggles: “Sign in” / “Create account”
- Subtitle differs by portal

### Controls
1. **Mode toggle:** Sign in | Sign up (segmented control)
2. **Sign up fields (both):** Full name, Email, Password (min 6)
3. **Sign up — student only:**
   - Student ID: exactly **12 digits** (e.g. `231003003137`), numeric input with live counter `X/12`
   - Semester (default “VI”), Branch (default “CSE”)
4. **Submit button:** Full width, indigo

### Messages
- Error: red text (validation, API errors)
- Success (signup): green text — student reminded to share ID with faculty; auto sign-in after signup

### Faculty vs student copy
| | Faculty | Student |
|---|---------|---------|
| Subtitle | Manage batches & campus announcements | Access notices, deadlines & AI assistant |
| Extra fields | None | Student ID, semester, branch |

### States
- Loading: button “Please wait…”
- Validation: 12-digit ID required for student signup

---

## Screen 3 — Faculty Dashboard

**Route:** `/faculty` (authenticated)  
**File:** `frontend/src/pages/FacultyApp.tsx` → `FacultyDashboard`

### Purpose
Main faculty hub: post announcements, manage batches, view campus feed.

### Header (sticky)
| Left | Right |
|------|-------|
| “AcadMind · Faculty” (violet) | System status badge |
| “Campus Manager” (h1) | User menu (name, role badge, sign out) |

### Profile error banner (conditional)
Amber alert with “Retry” if profile load fails.

### Main sections (top → bottom)

#### 3a. Post Composer
**Component:** `PostComposer.tsx`  
Facebook-style announcement creation.

| Element | Description |
|---------|-------------|
| Title | “Create announcement” |
| Subtitle | DigiCampus-style — notices, exams, assignments & resources |
| Batch select | Required dropdown |
| Subject select | Required; loads when batch selected |
| Textarea | Notice body (optional if file attached) |
| Upload button | Always visible; opens file picker |
| Post button | Publishes to selected batch + subject |

**Validation:** Must select batch + subject; need text OR file.

#### 3b. Two-column layout (lg: 3 + 2)

**Left — Your batches** (`BatchGrid.tsx`)
- “+ New batch” button (violet)
- Grid of batch cards OR empty state (“No batches yet…”)
- Each card: code, name, semester, branch, subject count, student count
- Click card → Batch Detail view

**Right — Campus feed** (`CampusFeed.tsx`, faculty API)
- List of recent announcements across faculty’s batches
- Refreshes when a new post is published

### Modal — Create Batch
**Component:** `CreateBatchModal.tsx`  
Overlay modal with fields: Name, Code, Semester, Branch. Cancel / Create.

### States
- Loading batches
- Empty batches
- API errors (red text)

---

## Screen 4 — Faculty Batch Detail

**Route:** `/faculty` (in-app; `selectedBatchId` state)  
**File:** `frontend/src/components/BatchDetail.tsx`

### Purpose
Manage one batch: view notices, subjects, and students.

### Navigation
- “← Back to dashboard” link (violet)

### Batch header
- Code (uppercase label)
- Batch name (h2)
- Meta: semester · branch · subject count · student count

### Tabs
| Tab | Content |
|-----|---------|
| **Notices** | List of posts for this batch (type badge, subject, due date, content/file) |
| **Subjects** | Subject list + “Add subject” form (name, code) |
| **Students** | Enrollment ID list + add/remove student |

### Students tab (important)
- **List:** Each row shows 12-digit Student ID (mono font) + **Remove** button (with confirm dialog)
- **Add form:** Full 12-digit ID input, digit counter, disabled until 12 digits
- Help text: linking ID connects student to batch for feed + AI queries

### States
- Loading batch
- Empty posts / subjects / students
- Error banner (red)

---

## Screen 5 — Student Dashboard

**Route:** `/student` (authenticated)  
**File:** `frontend/src/pages/StudentApp.tsx` → `StudentDashboard`

### Purpose
Student hub inspired by **DigiCampus**: batches, feed, AI, Jarvis.

### Header (sticky)
| Left | Right |
|------|-------|
| “AcadMind · Student” (sky) | System status badge |
| “DigiCampus” (h1) | User menu (+ Student ID if set) |

### Tab navigation
| Tab ID | Label | View |
|--------|-------|------|
| campus | Campus | Default |
| ai | Ask AI | Query assistant |
| jarvis | Jarvis | Screenshot upload |

Active tab: indigo background. Inactive: zinc text, hover bg.

---

## Screen 5a — Student tab: Campus

### Section 1 — My batches
**Component:** inline `MyBatches` in `StudentApp.tsx`

- Grid of enrolled batch cards (code, name, subject count, semester)
- **Empty state:** “Not enrolled in any batch yet. Ask faculty to add your Student ID.”

### Section 2 — Announcements & deadlines
**Component:** `CampusFeed.tsx` (student API)

- Same card layout as faculty feed
- Items from batches the student is enrolled in
- Badges by type, batch code, subject code, due date, file attachment

---

## Screen 5b — Student tab: Ask AI

**Component:** `QueryAssistantPanel.tsx`

### Purpose
Natural-language Q&A over enrolled batch data (Neo4j + Gemini).

### Layout
- Title: “Ask AcadMind AI”
- Subtitle: Query deadlines, exams & assignments from campus graph
- Textarea + “Ask” button
- Answer area (pre-wrap text, dark panel)
- Source citations list (title, subject, due date)

### Example prompts (placeholder)
- “When is the CN exam?”
- “What's due this week?”

### States
- Loading: “Searching…”
- Error message
- Empty until first query

---

## Screen 5c — Student tab: Jarvis

**Component:** `JarvisPanel.tsx`

### Purpose
Upload screenshots for OCR / event extraction (Phase 3 — **currently stub**).

### Layout
- Title: “Jarvis Memory”
- Subtitle: Upload screenshots from WhatsApp, email, or notice boards
- Large dashed upload zone (full width)
- Shows filename after selection
- Result message panel after upload

### States
- Loading: “Uploading…”
- Error / success message

---

## Shared components

### UserMenu (`UserMenu.tsx`)
Shown in faculty & student headers when profile loaded.

| Element | Description |
|---------|-------------|
| Name | Full name or email |
| Role badge | student (sky) / faculty (violet) / admin (amber) |
| Student ID | Mono text, student only |
| Sign out | Border button |

### StatusBadge (`StatusBadge.tsx`)
Backend health indicator in header.

| Status | Color |
|--------|-------|
| ok | Emerald |
| degraded | Amber |
| error / offline | Red |
| loading | Gray “…” |

### Card (`ui/Card.tsx`)
Base container for feeds, forms, batch tiles.

### CampusFeed (`CampusFeed.tsx`)
Reusable feed list; `api` prop: `"faculty"` | `"student"`.

Each item:
- Type badge
- Batch code, subject code
- Due date (amber, right-aligned)
- Title, content, file name

---

## User flows (for Stitch journey maps)

### Flow A — Faculty setup
```
Landing → Faculty → Sign up → Dashboard
→ Create batch (modal) → Open batch → Add subjects
→ Add students (12-digit IDs) → Post announcement (batch + subject + optional file)
```

### Flow B — Student onboarding
```
Landing → Student → Sign up (with 12-digit ID)
→ Faculty adds same ID to batch
→ Student sees batch + feed on Campus tab → Ask AI about notices
```

### Flow C — Parallel testing
```
Tab 1: /faculty (faculty session)
Tab 2: /student (student session)
Separate Supabase storage keys — sessions don't conflict
```

---

## API surface (per screen)

| Screen | Key endpoints |
|--------|---------------|
| Auth signup | `POST /api/v1/auth/signup` |
| Auth profile | `GET /api/v1/{faculty\|student}/me` |
| Faculty batches | `GET/POST /api/v1/faculty/batches` |
| Batch detail | `GET /api/v1/faculty/batches/{id}` |
| Add subject | `POST .../batches/{id}/subjects` |
| Add/remove student | `POST/DELETE .../batches/{id}/students[/{enrollment_id}]` |
| Create post | `POST /api/v1/faculty/posts` (multipart) |
| Faculty feed | `GET /api/v1/faculty/feed` |
| Student batches | `GET /api/v1/student/batches` |
| Student feed | `GET /api/v1/student/feed` |
| Ask AI | `POST /api/v1/student/query/chat` |
| Jarvis | `POST /api/v1/student/jarvis/upload` |
| Health | `GET /api/v1/health` |

---

## Redesign guidance for Stitch

### Keep
- Two-portal model (Faculty / Student) with distinct accent colors
- Dark modern aesthetic (DigiCampus / campus app feel)
- Post composer with **always-visible upload** (Facebook-style)
- 12-digit Student ID as first-class UI element
- Tab structure on student side (Campus / Ask AI / Jarvis)
- Batch detail tabs (Notices / Subjects / Students)
- Type-colored badges on feed items

### Improve (open to Stitch)
- Navigation hierarchy and breadcrumbs
- Mobile bottom nav for student tabs
- Richer empty states and onboarding illustrations
- Batch card visual hierarchy
- Post composer layout (inline vs modal on mobile)
- Loading skeletons instead of plain text
- Toast notifications for actions (add student, post, remove)
- Accessibility: focus states, contrast, form labels

### Do not add
- “Switch portal” link in authenticated headers (removed by design)
- Light theme requirement (dark is intentional unless product decides otherwise)
- Email confirmation step in signup flow

### Reference products
- **DigiCampus** — student feed, batches, announcements
- **Facebook** — post composer with persistent upload affordance
- **Modern SaaS dashboards** — sticky header, card grids, status indicators

---

## File → screen mapping

| File | Screen / section |
|------|------------------|
| `pages/LandingPage.tsx` | Landing |
| `components/AuthPage.tsx` | Faculty & student auth |
| `pages/FacultyApp.tsx` | Faculty shell + dashboard gate |
| `components/PostComposer.tsx` | Faculty announcement composer |
| `components/BatchGrid.tsx` | Faculty batch list |
| `components/CreateBatchModal.tsx` | Create batch modal |
| `components/BatchDetail.tsx` | Faculty batch detail |
| `components/CampusFeed.tsx` | Faculty & student feeds |
| `pages/StudentApp.tsx` | Student shell + dashboard + My Batches |
| `components/QueryAssistantPanel.tsx` | Ask AI tab |
| `components/JarvisPanel.tsx` | Jarvis tab |
| `components/UserMenu.tsx` | Header user menu |
| `components/StatusBadge.tsx` | Header health badge |
| `components/ui/Card.tsx` | Base card + badge variants |

---

## Glossary

| Term | Meaning |
|------|---------|
| Batch | A class group (e.g. CSE 6A, Sem VI) |
| Subject | Course within a batch (e.g. CN, SE) |
| Student ID | 12-digit institutional enrollment ID |
| Post / Notice | Faculty announcement (exam, assignment, notice, resource) |
| Campus feed | Chronological list of posts/events for user’s batches |
| DigiCampus | Student-facing brand name for the portal |

---

*Last updated: June 2026 — AcadMind Phase 2 frontend*
