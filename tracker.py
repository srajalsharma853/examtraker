"""
tracker.py
----------
Core logic of the ExamPrep Tracker:
- subjects (each with an exam date) and their syllabus topics
- topic status: Not Started -> In Progress -> Completed
- spaced revision reminders
- syllabus progress and exam countdown

SPACED REVISION RULE
    After a topic is completed, revise it again after a growing gap.
    REVISION_GAPS = [1, 3, 7, 14, 30] means:
      revision 1 is due 1 day after completion,
      revision 2 is due 3 days after revision 1,
      revision 3 is due 7 days after revision 2, and so on.
    Once every gap has been used, the topic is fully revised.
"""

from datetime import datetime, timedelta

from utils import (
    get_non_empty_string,
    get_future_date,
    get_choice_from_list,
    get_yes_no,
    today,
)
from storage import next_id

STATUSES = ["Not Started", "In Progress", "Completed"]
DIFFICULTIES = ["Easy", "Medium", "Hard"]
REVISION_GAPS = [1, 3, 7, 14, 30]   # days; customize to your own study style


# ---------------------------------------------------------------- HELPERS

def parse_date(text):
    """Convert a 'YYYY-MM-DD' string into a date object."""
    return datetime.strptime(text, "%Y-%m-%d").date()


def find_by_id(records, record_id):
    """Return the record with this id, or None."""
    for record in records:
        if record["id"] == record_id:
            return record
    return None


def ask_for_id(records, prompt, label):
    """Ask for an ID and check it exists. Returns the record, or None."""
    raw = input(prompt).strip()
    if not raw.isdigit():
        print("Please enter a numeric ID.")
        return None
    record = find_by_id(records, int(raw))
    if record is None:
        print(f"No {label} found with that ID.")
    return record


def topics_of(data, subject_id):
    """All topics belonging to one subject."""
    return [t for t in data["topics"] if t["subject_id"] == subject_id]


def progress_bar(percent, width=20):
    """Return a text bar such as [##########----------] 50%."""
    filled = int(width * percent / 100)
    return "[" + "#" * filled + "-" * (width - filled) + f"] {percent:.0f}%"


# ---------------------------------------------------------------- SUBJECTS

def add_subject(data):
    """Add a subject together with its exam date."""
    print("\n--- Add Subject ---")
    name = get_non_empty_string("Subject name: ")
    for s in data["subjects"]:
        if s["name"].lower() == name.lower():
            print("That subject already exists.")
            return
    exam_date = get_future_date("Exam date")
    subject = {"id": next_id(data["subjects"]), "name": name,
               "exam_date": exam_date.isoformat()}
    data["subjects"].append(subject)
    print(f"Subject added with ID {subject['id']}.")


def view_subjects(data):
    """List all subjects with exam date and days left."""
    if not data["subjects"]:
        print("\nNo subjects added yet.")
        return
    print("\n{:<4}{:<24}{:<13}{:<10}{:<8}".format(
        "ID", "Subject", "Exam date", "Days left", "Topics"))
    print("-" * 59)
    for s in data["subjects"]:
        days_left = (parse_date(s["exam_date"]) - today()).days
        shown = str(days_left) if days_left >= 0 else "passed"
        print("{:<4}{:<24}{:<13}{:<10}{:<8}".format(
            s["id"], s["name"][:23], s["exam_date"], shown,
            len(topics_of(data, s["id"]))))


def delete_subject(data):
    """Delete a subject and every topic inside it (after confirmation)."""
    view_subjects(data)
    if not data["subjects"]:
        return
    subject = ask_for_id(data["subjects"], "Enter subject ID to delete: ", "subject")
    if subject is None:
        return
    count = len(topics_of(data, subject["id"]))
    if get_yes_no(f"Delete '{subject['name']}' and its {count} topic(s)?"):
        data["topics"] = [t for t in data["topics"] if t["subject_id"] != subject["id"]]
        data["subjects"].remove(subject)
        print("Subject deleted.")


# ---------------------------------------------------------------- TOPICS

def add_topic(data):
    """Add a syllabus topic under an existing subject."""
    if not data["subjects"]:
        print("\nAdd a subject first.")
        return
    view_subjects(data)
    subject = ask_for_id(data["subjects"], "Subject ID for this topic: ", "subject")
    if subject is None:
        return

    name = get_non_empty_string("Topic name: ")
    difficulty = get_choice_from_list("Difficulty", DIFFICULTIES)
    topic = {
        "id": next_id(data["topics"]),
        "subject_id": subject["id"],
        "name": name,
        "difficulty": difficulty,
        "status": "Not Started",
        "completed_date": None,
        "revisions": 0,
        "last_revised": None,
    }
    data["topics"].append(topic)
    print(f"Topic added to {subject['name']} with ID {topic['id']}.")


def view_topics(data):
    """Show topics grouped by subject."""
    if not data["topics"]:
        print("\nNo topics added yet.")
        return
    for subject in data["subjects"]:
        topics = topics_of(data, subject["id"])
        if not topics:
            continue
        print(f"\n{subject['name']}  (exam {subject['exam_date']})")
        print("{:<4}{:<28}{:<9}{:<13}{:<10}".format(
            "ID", "Topic", "Level", "Status", "Revisions"))
        print("-" * 64)
        for t in topics:
            print("{:<4}{:<28}{:<9}{:<13}{}/{}".format(
                t["id"], t["name"][:27], t["difficulty"], t["status"],
                t["revisions"], len(REVISION_GAPS)))


def update_status(data):
    """Change a topic's status. Completing a topic records today's date."""
    view_topics(data)
    if not data["topics"]:
        return
    topic = ask_for_id(data["topics"], "Enter topic ID: ", "topic")
    if topic is None:
        return

    new_status = get_choice_from_list("New status", STATUSES)
    topic["status"] = new_status
    if new_status == "Completed":
        topic["completed_date"] = today().isoformat()
    else:
        # Moving back from Completed cancels its revision history.
        topic["completed_date"] = None
        topic["revisions"] = 0
        topic["last_revised"] = None
    print(f"'{topic['name']}' is now {new_status}.")


def delete_topic(data):
    """Delete a single topic."""
    view_topics(data)
    if not data["topics"]:
        return
    topic = ask_for_id(data["topics"], "Enter topic ID to delete: ", "topic")
    if topic is None:
        return
    if get_yes_no(f"Delete '{topic['name']}'?"):
        data["topics"].remove(topic)
        print("Topic deleted.")


# ---------------------------------------------------------------- REVISION

def next_revision_date(topic):
    """
    Return the date this topic is next due for revision, or None if it
    is not completed yet or every revision has been done.
    """
    if topic["status"] != "Completed":
        return None
    if topic["revisions"] >= len(REVISION_GAPS):
        return None

    # The gap counts from the last revision, or from completion if never revised.
    start_text = topic["last_revised"] or topic["completed_date"]
    gap = REVISION_GAPS[topic["revisions"]]
    return parse_date(start_text) + timedelta(days=gap)


def log_revision(data):
    """Record that the student revised a completed topic today."""
    completed = [t for t in data["topics"] if t["status"] == "Completed"]
    if not completed:
        print("\nNo completed topics yet. Complete a topic before revising it.")
        return

    print("\nCompleted topics:")
    for t in completed:
        print(f"  {t['id']}. {t['name']}  (revisions {t['revisions']}/{len(REVISION_GAPS)})")

    topic = ask_for_id(completed, "Enter topic ID you revised: ", "completed topic")
    if topic is None:
        return
    if topic["revisions"] >= len(REVISION_GAPS):
        print("This topic is already fully revised.")
        return

    topic["revisions"] += 1
    topic["last_revised"] = today().isoformat()
    print(f"Revision logged ({topic['revisions']}/{len(REVISION_GAPS)}).")
    due = next_revision_date(topic)
    if due:
        print(f"Next revision due on {due.isoformat()}.")
    else:
        print("Fully revised. Well done!")


def get_revision_reminders(data):
    """Return (topic, due_date) pairs that are due today or overdue, oldest first."""
    reminders = []
    for t in data["topics"]:
        due = next_revision_date(t)
        if due is not None and due <= today():
            reminders.append((t, due))
    reminders.sort(key=lambda pair: pair[1])
    return reminders


def view_revision_reminders(data):
    """Print topics that should be revised now."""
    reminders = get_revision_reminders(data)
    if not reminders:
        print("\nNothing to revise right now. You're up to date!")
        return
    print("\nTopics to revise:")
    for topic, due in reminders:
        subject = find_by_id(data["subjects"], topic["subject_id"])
        days_late = (today() - due).days
        note = "due today" if days_late == 0 else f"{days_late} day(s) overdue"
        print(f"  - {subject['name'] if subject else '?'}: {topic['name']}  [{note}]")


# ---------------------------------------------------------------- PROGRESS

def subject_progress(data, subject):
    """
    Return (completed, total, percent) for one subject.
    Percent is 0 when the subject has no topics (avoids dividing by zero).
    """
    topics = topics_of(data, subject["id"])
    total = len(topics)
    completed = len([t for t in topics if t["status"] == "Completed"])
    percent = (completed / total * 100) if total else 0.0
    return completed, total, percent


def view_progress(data):
    """Show syllabus completion and revision progress per subject."""
    if not data["subjects"]:
        print("\nNo subjects added yet.")
        return
    all_done, all_total = 0, 0
    print("\n--- Syllabus Progress ---")
    for s in data["subjects"]:
        done, total, percent = subject_progress(data, s)
        all_done += done
        all_total += total

        topics = topics_of(data, s["id"])
        revised = len([t for t in topics if t["revisions"] >= len(REVISION_GAPS)])
        print(f"\n{s['name']}")
        print(f"  Syllabus : {progress_bar(percent)}  ({done}/{total} topics)")
        print(f"  Fully revised topics: {revised}/{total}")

    overall = (all_done / all_total * 100) if all_total else 0.0
    print(f"\nOverall  : {progress_bar(overall)}  ({all_done}/{all_total} topics)")


# ---------------------------------------------------------------- COUNTDOWN

def view_countdown(data):
    """For each subject: days left, topics left, and the pace needed per day."""
    if not data["subjects"]:
        print("\nNo subjects added yet.")
        return
    print("\n--- Exam Countdown ---")
    ordered = sorted(data["subjects"], key=lambda s: s["exam_date"])
    for s in ordered:
        days_left = (parse_date(s["exam_date"]) - today()).days
        done, total, _ = subject_progress(data, s)
        remaining = total - done

        print(f"\n{s['name']}  (exam {s['exam_date']})")
        if days_left < 0:
            print("  Exam date has passed.")
        elif remaining == 0:
            print(f"  {days_left} day(s) left. Syllabus complete, keep revising!")
        elif days_left == 0:
            print(f"  Exam is TODAY with {remaining} topic(s) still incomplete.")
        else:
            pace = remaining / days_left
            print(f"  {days_left} day(s) left, {remaining} topic(s) to finish.")
            print(f"  Needed pace: {pace:.1f} topic(s) per day.")
            if pace > 1:
                print("  WARNING: you need more than one topic per day. Start now!")