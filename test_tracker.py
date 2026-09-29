"""
test_tracker.py
----------------
Simple tests you can run yourself:   python3 test_tracker.py
Each test feeds fake keyboard input into the real functions and checks the result.
"""

import unittest
from datetime import timedelta
from unittest.mock import patch

import tracker
import storage
from utils import today


def fresh_data():
    return storage.empty_data()


def feed(answers):
    """Pretend the user typed these answers, in order."""
    return patch("builtins.input", side_effect=answers)


class TestSubjects(unittest.TestCase):
    def test_add_subject_rejects_past_date(self):
        data = fresh_data()
        past = (today() - timedelta(days=1)).isoformat()
        future = (today() + timedelta(days=10)).isoformat()
        with feed(["Physics", past, future]):
            tracker.add_subject(data)
        self.assertEqual(data["subjects"][0]["exam_date"], future)

    def test_duplicate_subject_name_rejected(self):
        data = fresh_data()
        future = (today() + timedelta(days=10)).isoformat()
        with feed(["Physics", future]):
            tracker.add_subject(data)
        with feed(["Physics"]):
            tracker.add_subject(data)
        self.assertEqual(len(data["subjects"]), 1)

    def test_delete_subject_removes_its_topics(self):
        data = fresh_data()
        data["subjects"] = [{"id": 1, "name": "Physics",
                             "exam_date": (today() + timedelta(days=5)).isoformat()}]
        data["topics"] = [{"id": 1, "subject_id": 1, "name": "Motion",
                           "difficulty": "Easy", "status": "Not Started",
                           "completed_date": None, "revisions": 0, "last_revised": None}]
        with feed(["1", "y"]):
            tracker.delete_subject(data)
        self.assertEqual(data["subjects"], [])
        self.assertEqual(data["topics"], [])


class TestTopics(unittest.TestCase):
    def setUp(self):
        self.data = fresh_data()
        self.data["subjects"] = [{"id": 1, "name": "Physics",
                                  "exam_date": (today() + timedelta(days=20)).isoformat()}]

    def test_add_topic(self):
        with feed(["1", "Motion", "hard"]):
            tracker.add_topic(self.data)
        self.assertEqual(len(self.data["topics"]), 1)
        self.assertEqual(self.data["topics"][0]["difficulty"], "Hard")
        self.assertEqual(self.data["topics"][0]["status"], "Not Started")

    def test_completing_topic_sets_date(self):
        with feed(["1", "Motion", "easy"]):
            tracker.add_topic(self.data)
        with feed(["1", "completed"]):
            tracker.update_status(self.data)
        topic = self.data["topics"][0]
        self.assertEqual(topic["status"], "Completed")
        self.assertEqual(topic["completed_date"], today().isoformat())

    def test_reverting_from_completed_resets_revisions(self):
        with feed(["1", "Motion", "easy"]):
            tracker.add_topic(self.data)
        with feed(["1", "completed"]):
            tracker.update_status(self.data)
        topic = self.data["topics"][0]
        topic["revisions"] = 2
        with feed(["1", "in progress"]):
            tracker.update_status(self.data)
        self.assertEqual(topic["revisions"], 0)
        self.assertIsNone(topic["completed_date"])


class TestRevision(unittest.TestCase):
    def setUp(self):
        self.data = fresh_data()
        self.data["subjects"] = [{"id": 1, "name": "Physics",
                                  "exam_date": (today() + timedelta(days=30)).isoformat()}]
        self.data["topics"] = [{
            "id": 1, "subject_id": 1, "name": "Motion", "difficulty": "Medium",
            "status": "Completed", "completed_date": (today() - timedelta(days=5)).isoformat(),
            "revisions": 0, "last_revised": None,
        }]

    def test_next_revision_date_uses_first_gap(self):
        due = tracker.next_revision_date(self.data["topics"][0])
        expected = today() - timedelta(days=5) + timedelta(days=tracker.REVISION_GAPS[0])
        self.assertEqual(due, expected)

    def test_topic_not_started_has_no_revision_date(self):
        topic = {"status": "Not Started", "revisions": 0,
                 "completed_date": None, "last_revised": None}
        self.assertIsNone(tracker.next_revision_date(topic))

    def test_log_revision_advances_count_and_date(self):
        with feed(["1"]):
            tracker.log_revision(self.data)
        topic = self.data["topics"][0]
        self.assertEqual(topic["revisions"], 1)
        self.assertEqual(topic["last_revised"], today().isoformat())

    def test_fully_revised_topic_has_no_next_date(self):
        topic = self.data["topics"][0]
        topic["revisions"] = len(tracker.REVISION_GAPS)
        topic["last_revised"] = today().isoformat()
        self.assertIsNone(tracker.next_revision_date(topic))

    def test_reminder_includes_overdue_topic(self):
        topic = self.data["topics"][0]
        topic["completed_date"] = (today() - timedelta(days=10)).isoformat()  # gap[0]=1 day, so overdue
        reminders = tracker.get_revision_reminders(self.data)
        self.assertEqual(len(reminders), 1)
        self.assertEqual(reminders[0][0]["id"], 1)


class TestProgress(unittest.TestCase):
    def test_progress_with_zero_topics_is_zero_percent(self):
        data = fresh_data()
        subject = {"id": 1, "name": "Physics",
                   "exam_date": (today() + timedelta(days=5)).isoformat()}
        data["subjects"] = [subject]
        done, total, percent = tracker.subject_progress(data, subject)
        self.assertEqual((done, total, percent), (0, 0, 0.0))

    def test_progress_bar_format(self):
        bar = tracker.progress_bar(50, width=10)
        self.assertEqual(bar, "[#####-----] 50%")


class TestStorage(unittest.TestCase):
    def test_corrupted_file_recovers(self):
        import os
        storage.ensure_data_file()
        backup = None
        if os.path.exists(storage.DATA_FILE):
            with open(storage.DATA_FILE) as f:
                backup = f.read()
        try:
            with open(storage.DATA_FILE, "w") as f:
                f.write("{ broken json")
            self.assertEqual(storage.load_data(), storage.empty_data())
        finally:
            with open(storage.DATA_FILE, "w") as f:
                f.write(backup if backup is not None else "")


if __name__ == "__main__":
    unittest.main(verbosity=2)