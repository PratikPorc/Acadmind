// AcadMind unified knowledge graph — constraints & indexes (Phase 0)
// Run manually: cypher-shell -u neo4j -p acadmind_dev_password -f init_neo4j.cypher

CREATE CONSTRAINT department_id IF NOT EXISTS FOR (d:Department) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT subject_id IF NOT EXISTS FOR (s:Subject) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT faculty_id IF NOT EXISTS FOR (f:Faculty) REQUIRE f.id IS UNIQUE;
CREATE CONSTRAINT exam_id IF NOT EXISTS FOR (e:Exam) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT student_id IF NOT EXISTS FOR (st:Student) REQUIRE st.id IS UNIQUE;
CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT batch_id IF NOT EXISTS FOR (b:Batch) REQUIRE b.id IS UNIQUE;
CREATE CONSTRAINT post_id IF NOT EXISTS FOR (p:Post) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT resource_id IF NOT EXISTS FOR (r:Resource) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT event_id IF NOT EXISTS FOR (ev:Event) REQUIRE ev.id IS UNIQUE;
CREATE CONSTRAINT student_enrollment IF NOT EXISTS FOR (s:Student) REQUIRE s.enrollment_id IS UNIQUE;

CREATE INDEX subject_name IF NOT EXISTS FOR (s:Subject) ON (s.name);
CREATE INDEX event_due_date IF NOT EXISTS FOR (ev:Event) ON (ev.due_date);
CREATE INDEX post_event_category IF NOT EXISTS FOR (p:Post) ON (p.event_category);
CREATE INDEX event_category IF NOT EXISTS FOR (ev:Event) ON (ev.event_category);
