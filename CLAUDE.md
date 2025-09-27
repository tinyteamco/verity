# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a UXR (User Experience Research) platform MVP. The codebase currently contains:
- OpenAPI specification (`openapi.yaml`) defining the API contract
- Docker Compose configuration for local services
- Architecture and planning documentation

## Current Structure

### API Specification
The `openapi.yaml` file defines:
- Authentication using Firebase JWT tokens with bearer auth
- Two tenant types: `company` and `interviewee`
- Endpoints for studies, interviews, recordings, transcripts, and summaries
- Role-based access with roles: owner|admin|member

### Infrastructure
`docker-compose.yml` defines these services:
- PostgreSQL 16 (port 5432)
- MinIO object storage (ports 9000/9001)
- Firebase Auth emulator (port 9099)
- API service (port 8000) - references a Dockerfile that doesn't exist yet

### Documentation Structure
- `/docs/001-overview/` - MVP information architecture and UXR project details
- `/docs/002-architecture/` - Technical architecture decisions and patterns
- `/docs/003-plans/` - Implementation plans and roadmaps