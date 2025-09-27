# UXR Project Summary – Initial Context

This document summarizes the **application concept and use case** for the UXR startup, so future collaborators can quickly understand what we are building without needing to re-read all chat history.

---

## Vision
A B2B SaaS platform that enables organizations to rapidly conduct **user research studies** through automated AI agents. Organizations can test ideas and iterate quickly, while interviewees have a dedicated experience to participate in studies, manage their data, and view their past contributions.

---

## Primary Users

1. **Organization Users**  
   - Employees of client organizations who log in to design and run studies.  
   - All organization users currently have the same permissions.  
   - Key actions: create/manage studies, write interview guides, review interviews, and analyze study summaries.

2. **Interviewees**  
   - Individuals who participate in research studies.  
   - They maintain a permanent account and profile.  
   - Key actions: accept study invitations, complete interviews, review their past interviews, and manage privacy preferences.

---

## Core Concepts

- **Study**: The central object organizations create. A study is a container for interviews and results.
- **Interview Guide**: Written in markdown, defines the flow/questions an AI agent uses to conduct interviews.
- **Interview**: Occurs when an interviewee participates in a study. Each produces an audio recording, transcript, highlights, and an interview summary.
- **Interview Summary**: A concise synthesis of a single interview.
- **Highlights**: Key segments from audio recordings.
- **Study Summary**: A synthesis across all interviews in a study (text plus optional auto-generated highlight reels).

---

## User Flows

- **Organization flow**: Login → view Studies list (home) → create Study → author Interview Guide → share study link with potential interviewees → monitor incoming Interviews → read Interview Summaries → view/update Study Summary.

- **Interviewee flow**: Login → view invitations → complete Interview → see personal history of past Interviews and assets.

---

## Marketplace Nature
- Interviewees are global, not tied to one organization.  
- They may participate in many studies across different organizations.  
- The platform is thus a two-sided marketplace: organizations on one side, interviewees on the other.

---

## Current MVP Scope (aligned with IA v3)
- Only **audio recordings** (no video yet).
- **One version** of summaries per study and per interview (no version history yet).
- Minimal attributes for each entity (YAGNI approach).  
- Study links are shared directly (no dedicated invite/eligibility system yet).
- Highlights reels exist conceptually but are auto-generated, not persistent entities.

---

## Intentionally Deferred
- Billing, subscription, and organization plan management.
- Role-based permissions for organization users.
- Advanced marketplace features (matching, reputation, incentives).
- Rich consent/PII workflows and compliance tooling.
- Video support (recordings, highlights, reels).
- Reels as persistent, user-editable assets.
- Analytics, dashboards, tagging, and sentiment analysis.
- Lifecycle policies (archival, soft deletes).

---

**Next Steps:** This summary should evolve as product scope grows. It complements the **MVP Information Architecture (v3)** document, providing context for *why* these entities exist and how they fit into the bigger vision.