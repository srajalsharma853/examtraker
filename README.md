# examtracker
A terminal-based Python program that tracks syllabus completion and spaced
revision across your exam subjects: what's done, what's left, what needs
revising, and how many topics a day you need to finish in time.

## Requirements

- Python 3.8 or newer
- No external packages (standard library only)

## How to Run

From inside this folder:

python3 main.py

(Use `python main.py` on Windows.) Always run `main.py`; the other files are
supporting modules. The data file `data/examprep.json` is created automatically.

## Run the Tests

python3 test_tracker.py

## Features

1. Add Subject - Add a subject with its exam date
2. View Subjects - Exam date and days left for every subject
3. Add Topic - Add a syllabus topic to a subject, with a difficulty level
4. View Topics - Topics grouped by subject, with status and revision count
5. Update Topic Status - Not Started → In Progress → Completed
6. Log a Revision - Record that you revised a completed topic today
7. Revision Reminders - Topics due or overdue for their next revision
8. Syllabus Progress - Per-subject and overall completion progress bars
9. Exam Countdown - Days left and the topics-per-day pace you need
10. Delete Topic - Remove a single topic
11. Delete Subject - Remove a subject and all its topics
12. Exit - Saves and quits

## How Spaced Revision Works

Completing a topic starts a revision schedule using growing gaps:

REVISION_GAPS = [1, 3, 7, 14, 30]

- Revision 1 is due 1 day after the topic is completed.
- Revision 2 is due 3 days after revision 1 is logged.
- Revision 3 is due 7 days after revision 2.
- Revision 4 is due 14 days after revision 3.
- Revision 5 is due 30 days after revision 4.
- After all 5 revisions are logged, the topic is considered fully revised.

Moving a topic back out of "Completed" resets its revision count.

## Exam Pace Calculation

For each subject:

pace = topics_remaining / days_left

If the pace is above 1 topic per day, the program warns you that you're
behind schedule.

## Project Structure

examprep-tracker/
├── main.py          # menu loop (entry point)
├── tracker.py       # subjects, topics, revision logic, progress, countdown
├── storage.py       # JSON load/save
├── utils.py         # input validation and display helpers
├── test_tracker.py  # runnable tests
├── data/
│   └── examprep.json # created automatically
├── README.md
└── requirements.txt

## Data Storage

One JSON file holds two lists: `subjects` (name, exam date) and `topics`
(subject_id, name, difficulty, status, completed_date, revisions,
last_revised).

Data is saved after every action, and a corrupted file is replaced with empty
data instead of crashing the program.

## Input Validation

Empty names, invalid or past-dated exam dates, non-numeric IDs, duplicate
subject names, invalid menu choices, and non-existent IDs are all rejected
with a message and a re-prompt.

## Limitations

- Single-user, no login system
- Revision gaps are fixed constants, not per-topic customizable
- No calendar/notification integration
- Reminders only show inside the app

## Future Improvements

- Per-topic custom revision schedules
- Export progress to CSV or a printable report
- Multiple exam attempts / subject history
- Daily study-time logging alongside topic status