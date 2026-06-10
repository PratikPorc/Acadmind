# AcadMind Frontend — Page & Screen Reference

> **Purpose:** This document describes every screen, layout, and interaction in the AcadMind frontend. Use it as a brief for **Stitch** (or any design tool) to redesign the UI while preserving functionality and user flows.

---

## Product Overview

**AcadMind** is an AI-powered campus platform for **Techno India University**. It has two separate portals:

| Portal | Route | Brand Name | Primary User |
|--------|-------|------------|--------------|
| Faculty | `/faculty` | **Campus Manager** | Teachers / faculty |
| Student | `/student` | **Scholar Portal** | Students |

*Note: The Student brand name is loaded dynamically from `frontend/src/lib/branding.ts` as `STUDENT_PORTAL_NAME`.*

Both portals share the same elegant light theme and design language but use different subtle accent colors (violet vs sky/teal blue) to differentiate user roles.

**Core features:**
- Faculty creates batches, subjects, and campus notices categorized into Academic, Cultural, Technical, and Global.
- Faculty assigns students to batches by their **12-digit institutional Student ID**.
- Students view campus notices filtered by Academic (subjects they are enrolled in), Cultural, Technical, and Global categories.
- Students can filter notices in a sidebar by specific subjects, clubs, or technical domains.
- ASK Jarvis — a RAG-powered query assistant that allows students to query the campus knowledge graph conversationally.

**Important:** There is **no “Switch portal” button** in authenticated headers. Users enter via the landing page (`/`) and choose their portal.

---

## Tech Stack (Constraints for Redesign)

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

## Design System (Premium Light Theme)

To eliminate any "slop AI" vibe, we avoid over-saturated neon colors, heavy card shadows, and floating glow effects. The design should resemble high-end developer and productivity tools (e.g., Linear, Notion, or Stripe) with clean spacing, sharp alignments, thin borders, and subtle interactive states.

### Core Theme Colors
- **Page Background:** `#F8FAFC` (slate-50) — clean, soft off-white canvas.
- **Surface / Cards:** `#FFFFFF` (white) — clear containment of information.
- **Borders:** `#E2E8F0` (slate-200) — thin, low-contrast separator lines.
- **Primary Text:** `#0F172A` (slate-900) — high-contrast charcoal for titles and labels.
- **Muted Text:** `#64748B` (slate-500) — soft gray for secondary info, timestamps, and placeholders.
- **Font:** Inter (body text), Outfit (headlines).

### Accents
| Token | Hex / Tailwind | Usage |
|-------|----------------|-------|
| Faculty Accent | `#7C3AED` / violet-600 | Faculty labels, batch codes, headers |
| Student Accent | `#0284C7` / sky-600 | Student labels, batch codes, navigation |
| Primary Action | `#4F46E5` / indigo-600 | Primary buttons, active tabs |
| Success | `#10B981` / emerald-600 | Success messages, online/ok status |
| Warning | `#D97706` / amber-600 | Due dates, urgent alerts |
| Error | `#EF4444` / red-600 | Form and API errors |

### Reusable Patterns
- **Card:** Rounded xl (`rounded-xl`), border `slate-200`, background `white`, elevated with a subtle shadow (`shadow-sm`).
- **Input:** Rounded lg (`rounded-lg`), border `slate-300`, background `white`, focus border `indigo-500` with light blue outline ring.
- **Pill Badges:** Rounded-full, high-density colors with very low-saturation, light backgrounds for high readability:
  - **Academic:** `#EEF2F6` bg, `#475569` text (slate)
  - **Cultural:** `#FDF2F8` bg, `#BE185D` text (fuchsia)
  - **Technical:** `#ECFEFF` bg, `#0E7490` text (cyan)
  - **Global:** `#F0FDF4` bg, `#15803D` text (green)
  - **Exam:** `#FEE2E2` bg, `#B91C1C` text (red)
  - **Assignment:** `#FEF3C7` bg, `#B45309` text (amber)
- **Header:** Sticky `white` with bottom border `slate-200`, backdrop blur effect where content scrolls behind.

---

## Route Map

```
/                    → Landing Page (portal picker)
/faculty             → Faculty Auth OR Faculty Dashboard
/faculty/*           → Same (state-driven dashboard views)
/student             → Student Auth OR Student Dashboard
/student/*           → Same (tab-based views)
*                    → Redirect to /
```

Authenticated views are managed inside their respective portal root pages (`/faculty` and `/student`) using React state.

---

## Screen 1 — Landing Page

**Route:** `/`  
**File:** `frontend/src/pages/LandingPage.tsx`  
**Auth:** None

### Purpose
Entry point for TIU students and faculty to select their respective portals.

### Layout & Style
- Clean, centered grid layout with generous vertical padding.
- Institution Label: "Techno India University" in small, uppercase tracking-wide slate-500.
- Hero Title: **AcadMind** in large, bold Outfit font (deep charcoal `#0F172A`).
- Subtitle: "Knowledge graph campus platform — academic, cultural & technical notices with RAG-powered ASK Jarvis" (medium slate-600).
- Portal Selection: Two large, side-by-side interactive cards (`max-w-xl` total grid).
  - **Faculty Card:**
    - Label: "Faculty" (violet-600)
    - Title: "Campus Manager"
    - Subtitle: "Batches · subjects · academic, cultural & technical notices"
    - Hover: Soft violet border shift and minimal slate shadow increase.
  - **Student Card:**
    - Label: "Student" (sky-600)
    - Title: "Scholar Portal"
    - Subtitle: "Campus feed · subjects & events · ASK Jarvis RAG"
    - Hover: Soft sky blue border shift.
- Footer Note: "Open both portals in separate tabs to test faculty & student in parallel" (slate-400).

---

## Screen 2 — Auth (Sign In / Sign Up)

**Route:** `/faculty` or `/student` (when unauthenticated)  
**File:** `frontend/src/components/AuthPage.tsx`  
**Auth:** Supabase email/password; signup uses auto-confirmation.

### Layout & Style
- Centered card (`max-w-md`) on soft grey background canvas.
- Portal identity label: "Faculty Portal" (violet-600) or "Scholar Portal" (sky-600).
- Mode Selector: Segmented controls (Sign in / Create account) with a clean white/grey layout.
- Fields:
  - Sign up: Full Name, Email, Password.
  - Student Sign up extra fields:
    - Student ID: exactly **12 digits** (numeric with live counter `X/12`).
    - Semester (default "VI"), Branch (default "CSE").
- Submit Button: Full-width indigo-600 button with a clean hover state.
- Validation and messages shown in clear, clean red (errors) or emerald (success).

---

## Screen 3 — Faculty Dashboard

**Route:** `/faculty` (authenticated)  
**File:** `frontend/src/pages/FacultyApp.tsx`

### Header
- Sticky, thin border, shadowless white bar.
- Left: "AcadMind · Faculty" (violet-600) + "Campus Manager" title.
- Right: Health Status badge (emerald, amber, or red dots) + User Menu (user name, "faculty" role badge, and Sign Out button).

### Main Content (Grid layout)
1. **Post Composer (`PostComposer.tsx`):**
   - Labeled "Post campus notice".
   - Category selector buttons: **Academic**, **Cultural**, **Technical**, **Global**.
   - Input dropdowns change contextually based on category selection:
     - *Academic:* Dropdown for Batch selection and Subject selection.
     - *Cultural:* Dropdown for Batch and Club selection (e.g. Dance Club, Music Club).
     - *Technical:* Dropdown for Batch and Technical Domain selection (e.g. AI & ML, Web Dev).
     - *Global:* Dropdown for Batch and Global Scope (Academic, Cultural, Technical).
   - Textarea: Clean box to write notice contents. Placeholder text changes dynamically with the selected category.
   - Submit: Labeled "Post notice".
2. **Two-Column Dashboard Grid:**
   - **Left Column (Your Batches):** Labeled "+ New batch". A grid of batch cards showing Code, Name, Semester, Branch, and student/subject counts. Clicking a batch card launches the Batch Detail view.
   - **Right Column (Campus Feed):** Shows the recent feed items posted by the faculty. Divided into sections by category.

---

## Screen 4 — Faculty Batch Detail

**Route:** `/faculty` (in-app state `selectedBatchId`)  
**File:** `frontend/src/components/BatchDetail.tsx`

### Purpose
Manage subjects, view notices, and link student enrollments.

### Layout
- Nav link: "← Back to dashboard" in violet.
- Batch Header: Upper-case code, descriptive name, and semester/branch statistics.
- Tab selector:
  - **Notices:** Vertical timeline of notices posted to this batch (displays category badges, content, and dates).
  - **Subjects:** Grid of subjects and form to add a new subject (code, name).
  - **Students:** List of linked 12-digit student IDs with confirmation dialog to remove them, plus an "Add student by ID" form (with numeric-only input and counter).

---

## Screen 5 — Student Dashboard

**Route:** `/student` (authenticated)  
**File:** `frontend/src/pages/StudentApp.tsx`

### Header
- Sticky white bar.
- Left: "AcadMind · Student" (sky-600) + "Scholar Portal" title.
- Right: Health badge + User Menu (name, role badge, student ID, and Sign Out).

### Navigation
Two main tab buttons:
- **Campus** (Default)
- **ASK Jarvis** (RAG assistant)

---

## Screen 5a — Student Tab: Campus

**File:** `frontend/src/components/StudentCampusPanel.tsx`

### Layout
- Top navigation bar containing filtering category tabs: **Academic**, **Cultural Events**, **Technical Events**, **Global Updates**.
- Sub-filters:
  - Except under "Global Updates", a two-column sidebar layout is used:
    - **Sidebar (Filters):** Labeled "My Subjects", "Clubs", or "Domains" containing selection filters.
    - **Main Content:** A feed of notices filtered by the selected category and sidebar filter.
- Notices are rendered as card items (`CampusFeed.tsx`) showing type badges (exam, notice, assignment), categories, batch codes, dates, titles, and body texts.

---

## Screen 5b — Student Tab: ASK Jarvis

**File:** `frontend/src/components/QueryAssistantPanel.tsx`

### Purpose
Conversational Q&A (RAG) assistant grounded in Neo4j knowledge graph notices.

### Layout
- Labeled "ASK Jarvis".
- Description: "RAG-powered answers from the campus knowledge graph — academic, cultural & technical notices seeded by faculty".
- Textarea to ask questions (e.g. "When is the CN exam? Any hackathons this month?").
- Search button: "ASK Jarvis" (changes to "Searching graph..." when active).
- Answer panel: Clean light card display showing formatted answers.
- Source Citations: Bulleted list showing titles, categories, subjects, and due dates of the notices that served as sources.

---

## Redesign Guidance for Stitch

### Keep
- Role-based accent theme (Violet for Faculty, Sky/Teal for Student, Indigo for core system controls).
- Clean layouts, dynamic 12-digit student ID structures, and sidebar filter elements.
- The dynamic loading of the Scholar Portal title.
- Notice categories (Academic, Cultural, Technical, Global) and their distinct badge styling.

### Improve
- Transition the entire layout to a premium **Light Mode** design system.
- Use a cohesive typography layout (Outfit/Inter) with refined letter-spacing.
- Add soft margins, light borders (`slate-200`), and clean micro-shadows (`shadow-sm`) instead of high-glow borders.
- Provide neat loading skeletons for notice feeds and AI search responses.

### Do Not Add
- Floating glassmorphic blur overlays that obstruct content.
- Saturated neon backgrounds or dark backgrounds.
- Unnecessary file upload elements (since files have been removed from the backend database schema).
