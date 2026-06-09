# AcadMind — Faculty → Batch → Post Workflow

## Overview

```
Faculty login
    └── Create / manage Batches (shown as tiles)
            ├── Add students by Supabase User ID
            ├── Create subjects (CN, SE, DS, …)
            └── Create Post
                    ├── Write notice in natural language
                    │     e.g. "CN exam on 15th July"
                    │     e.g. "Assignment 4 of SE submit by 5th June"
                    └── Upload document / study material
                            │
                            ▼
                    Gemini parses → batch + subject + event type + date
                            │
                            ▼
                    Neo4j seeded (Post, Event, Resource nodes)
                            │
                            ▼
Student asks Query Assistant → retrieval from Neo4j → answer
```

## Neo4j Graph (Phase 2)

```
(Faculty)-[:TEACHES]->(Batch)-[:HAS_SUBJECT]->(Subject)
(Student)-[:MEMBER_OF]->(Batch)
(Post)-[:FOR_BATCH]->(Batch)
(Post)-[:FOR_SUBJECT]->(Subject)
(Post)-[:CREATED_BY]->(Faculty)
(Event)-[:FROM_POST]->(Post)
(Event)-[:BELONGS_TO]->(Subject)
(Event)-[:IN_BATCH]->(Batch)
(Resource)-[:FOR_BATCH]->(Batch)
(Resource)-[:FOR_SUBJECT]->(Subject)
(Resource)-[:FROM_POST]->(Post)
```

## Roles

| Role | Capabilities |
|------|--------------|
| **Faculty** | Create batches, add students by ID, create subjects, post notices/resources |
| **Student** | View enrolled batches (future), ask Query Assistant about deadlines & academics |

## Student ID

Students copy their **User ID** from the profile menu. Faculty paste it when adding a student to a batch.

## Notice parsing

Gemini receives the notice text + list of subjects in the batch and returns structured fields. The system matches subject aliases (e.g. CN → Computer Networks) and writes `Event` or `Resource` nodes linked to the correct batch and subject.
