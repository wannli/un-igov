# UI/UX Analysis of igov.un.org

**Date:** January 25, 2026

**Analyst:** UI/UX Review

---

## Executive Summary

igov.un.org serves as the "Portal to the work of intergovernmental bodies" for the United Nations, providing access to General Assembly, ECOSOC, and Conference information. While functional, there are significant opportunities to improve user-friendliness through targeted enhancements to the homepage, navigation, information architecture, and visual design.

---

## Critical Issues

### 1. Homepage Problems

**Issue:** Empty landing page with no content or guidance

- The homepage (igov.un.org/home-page) shows virtually no content - just the header, navigation, and footer
- No welcome message, quick links, featured content, or guidance for first-time users
- Users arriving at the site have no immediate understanding of what they can do here
- Missing search functionality on homepage - no prominent search bar for finding resolutions, documents, or meetings

**Impact:** High bounce rate from confused first-time visitors who don't understand the site's purpose

**Location:** `templates/index.html`

---

### 2. Navigation Issues

**Issue A:** Dropdown menus not working properly

- The main navigation dropdowns (General Assembly, ECOSOC, Conferences) don't visually expand when clicked
- Users must know the sub-links exist or manually navigate via URL
- The dropdown toggle indicators (chevron icons) don't provide clear feedback

**Impact:** Users cannot discover available sections easily

**Location:** `templates/base.html` - main navigation component

**Issue B:** Inconsistent external linking

- The Sixth Committee links to an external site (www.un.org/en/ga/sixth/)
- All other committees stay on igov.un.org domain
- No explanation or warning that users are leaving the site

**Impact:** User confusion, broken navigation expectations

**Location:** `templates/committee.html` - hardcoded link

**Issue C:** Deep nesting without clear context

- URL structure (e.g., `/ga/plenary/80/resolutions`) requires users to know the hierarchy
- No breadcrumb trail that is fully clickable until you're deep in the structure
- Session context lost when navigating between sections

**Impact:** Users get lost in the hierarchy; difficult to navigate back up

---

### 3. Content Display Problems

**Issue A:** Rendering bug on Agenda Items page

- Text displays as "(a)(g)(e)(n)(d)(a)-(i)(t)(e)(m)(s)" instead of "agenda-items"
- Likely a character-by-character parsing error in the routing or template

**Impact:** Broken user experience, erodes trust in the site

**Location:** Route `/agenda-items` - character escaping issue

**Issue B:** Dense data tables with poor readability

- Resolutions and Proposals pages show massive tables with small text
- Many columns with no visual hierarchy
- Critical information gets lost in the dense display
- Tables not responsive for mobile devices

**Impact:** Users cannot quickly scan and find relevant information

**Location:** `templates/decisions.html`, `templates/proposals.html`

**Issue C:** No pagination or lazy loading

- Meetings list shows 100+ items in a single scroll
- No pagination controls visible
- No "load more" functionality
- Difficult to navigate to older or specific meetings

**Impact:** Information overload, poor performance with large datasets

**Location:** `templates/meetings.html`

**Issue D:** Expand/collapse indicators are invisible

- The "+" icons for meeting details are nearly invisible
- No visible labels or tooltips
- Users don't know content can be expanded

**Impact:** Hidden functionality, users miss detailed information

**Location:** `templates/meetings.html` - expand/collapse component

---

### 4. Session Selector UX

**Issue:** Inconsistent session naming conventions

| Body | Format | Example |
|------|--------|---------|
| General Assembly | Ordinal text | "Eightieth session" |
| ECOSOC | Years | "2024, 2025, 2026" |
| CSW | Abbreviated ordinals | "SIXTY-NINTH", "SEVENTIETH" |

**Impact:** Cognitive load when switching between different bodies; inconsistent mental model

**Location:** `templates/ga_plenary.html`, `templates/ecosoc_body.html`, `templates/committee.html`

---

## Moderate Issues

### 5. Information Architecture Deficiencies

**Issue A:** Lack of cross-referencing between content types

- Resolutions don't link to related meetings where they were adopted
- Meetings don't link to associated documents or agenda items
- No relationship mapping between different content types

**Impact:** Users must manually search to find related information

**Issue B:** No search/filter functionality on listing pages

- Documents page has filter categories but no search input
- Cannot quickly find specific resolutions or documents
- Users must scroll through lengthy lists

**Impact:** Poor discoverability, time wasted browsing

**Location:** `templates/documents.html`

**Issue C:** Session switching resets context

- Changing sessions returns you to the parent page
- Not the equivalent sub-page in the new session
- Example: Viewing resolutions for session 79, switch to 80, land on plenary page not resolutions

**Impact:** Disrupted workflow, frustration when comparing sessions

---

### 6. Visual Design Deficiencies

**Issue A:** Minimal visual hierarchy

- Headers, body text, and labels all appear similar in weight
- No distinction between primary, secondary, and tertiary information
- Important content doesn't stand out

**Impact:** Difficulty scanning and prioritizing information

**Location:** `static/css/` - stylesheets

**Issue B:** Abstract card icons

- Six "cards" on session pages (Meetings, Agenda items, Documents, etc.) use abstract icons
- Icons don't clearly communicate what each section contains
- No text labels alongside icons

**Impact:** Icon interpretation requires cognitive effort; unclear navigation

**Location:** `templates/ga_plenary.html`, `templates/ecosoc_body.html`

**Issue C:** Poor link color contrast

- Blue-on-blue links don't stand out enough from surrounding text
- Visually impaired users may have difficulty identifying clickable elements
- Not meeting WCAG AA contrast guidelines

**Impact:** Accessibility issues, poor discoverability

**Location:** `static/css/` - link color variables

**Issue D:** No status indicators

- Upcoming meetings vs past meetings only differentiated by a small "Past meetings" header
- No color coding, icons, or visual distinction
- Cancelled meetings not visually highlighted

**Impact:** Users must read each meeting title to understand status

**Location:** `templates/meetings.html`

---

### 7. Accessibility Concerns

**Issue A:** Unclear language switcher

- Languages in the header are text-only with no clear indication they're clickable
- No visual distinction from regular text
- Users may not realize they can change language

**Impact:** Non-English speakers cannot easily switch languages

**Location:** `templates/base.html` - language switcher component

**Issue B:** Missing button labels

- Many buttons (filter toggles, expand/collapse) have no visible text labels
- Only icons without aria-labels or tooltips
- Screen reader users cannot understand button purpose

**Impact:** Inaccessible to keyboard and screen reader users

**Location:** All template files - icon-only buttons

**Issue C:** Unclear keyboard focus states

- Tab focus states not visible during keyboard navigation testing
- No outline or visual indicator when focusing on interactive elements

**Impact:** Keyboard users cannot navigate effectively

**Location:** `static/css/` - focus state styles

---

## Minor Issues

### 8. Footer & Branding

**Issue:** Minimal footer with only copyright info

- No sitemap for easy navigation
- No quick links to popular sections
- No contact information or help resources
- No social media or newsletter signup

**Impact:** Missed opportunity for user guidance and engagement

**Location:** `templates/base.html` - footer section

---

### 9. Mobile Responsiveness

**Issue A:** Tables overflow viewport

- Wide data tables (Proposals, Resolutions) require horizontal scrolling on mobile
- No card-based alternative layout for small screens
- Dense tables are unreadable on mobile devices

**Impact:** Poor mobile experience, most users may access via mobile

**Location:** `templates/decisions.html`, `templates/proposals.html`, `templates/documents.html`

**Issue B:** Navigation behavior unclear on mobile

- Hamburger menu exists but dropdown behavior unclear on smaller screens
- Touch targets may be too small for finger navigation
- No mobile-specific navigation patterns

**Impact:** Mobile users struggle to navigate the site

**Location:** `templates/base.html` - mobile navigation

---

## Recommendations by Priority

### High Priority (Quick Wins)

| # | Recommendation | Files to Modify |
|---|----------------|-----------------|
| 1 | Add homepage content: dashboard with "Latest Resolutions," "Upcoming Meetings," "Quick Links," and prominent search bar | `templates/index.html` |
| 2 | Fix the agenda-items rendering bug - investigate character parsing | Router/template engine |
| 3 | Add visible labels or tooltips to all icon-only buttons | All template files |
| 4 | Standardize session naming convention across all bodies | `templates/ga_plenary.html`, `templates/ecosoc_body.html`, `templates/committee.html` |

### Medium Priority (UX Improvements)

| # | Recommendation | Files to Modify |
|---|----------------|-----------------|
| 5 | Implement global search across all sessions, bodies, and document types | New search component, `templates/index.html` |
| 6 | Add pagination and lazy loading to long lists with search/filter | `templates/meetings.html`, `templates/documents.html` |
| 7 | Create visual status indicators (color/icons) for meeting types and status | `templates/meetings.html`, `static/css/` |
| 8 | Cross-link related content: resolutions to meetings, meetings to agenda items | All template files |
| 9 | Fix dropdown navigation - ensure visual expansion on hover/click | `templates/base.html` |

### Lower Priority (Design Polish)

| # | Recommendation | Files to Modify |
|---|----------------|-----------------|
| 10 | Redesign data tables: card-based mobile layout, collapsible rows | `templates/decisions.html`, `templates/proposals.html` |
| 11 | Improve card icons with text labels or more descriptive visuals | `templates/ga_plenary.html`, `templates/ecosoc_body.html` |
| 12 | Add comprehensive footer with sitemap, contact, help links | `templates/base.html` |
| 13 | Create onboarding flow explaining igov.un.org for first-time visitors | `templates/index.html`, `templates/base.html` |

---

## Technical Notes

### Current Stack

- Backend: Python-based (likely Flask or similar)
- Templates: Jinja2 HTML templates
- Styling: CSS with Bootstrap-like utility classes
- Static assets: CSS and JS in `static/` directory

### Files Structure

```
un-igov/
├── templates/
│   ├── base.html           # Main layout template
│   ├── index.html          # Homepage
│   ├── ga_plenary.html     # GA Plenary section
│   ├── committee.html      # Committee pages
│   ├── ecosoc_body.html    # ECOSOC bodies
│   ├── conference.html     # Conference pages
│   ├── meetings.html       # Meetings listing
│   ├── meeting.html        # Single meeting details
│   ├── documents.html      # Documents listing
│   ├── decisions.html      # Decisions listing
│   ├── proposals.html      # Proposals listing
│   ├── agenda.html         # Agenda items
│   └── macros.html         # Reusable template macros
├── static/
│   ├── css/                # Stylesheets
│   └── js/                 # JavaScript files
└── docs/
    └── ui-ux-analysis.md   # This file
```

---

## Summary

igov.un.org has the data and structure to be a powerful resource for accessing UN intergovernmental body information, but the current implementation prioritizes technical functionality over user experience. The empty homepage, navigation issues, and dense data presentation create barriers for users who need to quickly find UN documents, resolutions, or meeting information.

The high-priority recommendations focus on:
1. Adding content and search to the empty homepage
2. Fixing critical bugs (agenda-items rendering)
3. Making navigation discoverable and consistent
4. Adding visual hierarchy and accessibility improvements

Implementing these changes would significantly improve usability without requiring major architectural changes, making the portal more accessible to diplomats, researchers, journalists, and the general public who need to access UN intergovernmental proceedings.

---

*End of Analysis*
