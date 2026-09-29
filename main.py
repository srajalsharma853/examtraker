"""
main.py
-------
Entry point of the ExamPrep Tracker.
Run from the project folder with:   python3 main.py
"""

from utils import print_header, pause, get_menu_choice
from storage import load_data, save_data
import tracker

MENU = """
===== EXAMPREP TRACKER =====

 1. Add Subject (with exam date)
 2. View Subjects
 3. Add Topic
 4. View Topics
 5. Update Topic Status
 6. Log a Revision
 7. Revision Reminders
 8. Syllabus Progress
 9. Exam Countdown
10. Delete Topic
11. Delete Subject
12. Exit
"""


def main():
    data = load_data()
    choices = [str(n) for n in range(1, 13)]

    while True:
        print(MENU)
        choice = get_menu_choice("Choose an option (1-12): ", choices)

        if choice == "1":
            tracker.add_subject(data)
        elif choice == "2":
            print_header("SUBJECTS")
            tracker.view_subjects(data)
        elif choice == "3":
            tracker.add_topic(data)
        elif choice == "4":
            print_header("TOPICS")
            tracker.view_topics(data)
        elif choice == "5":
            print_header("UPDATE TOPIC STATUS")
            tracker.update_status(data)
        elif choice == "6":
            print_header("LOG A REVISION")
            tracker.log_revision(data)
        elif choice == "7":
            print_header("REVISION REMINDERS")
            tracker.view_revision_reminders(data)
        elif choice == "8":
            print_header("SYLLABUS PROGRESS")
            tracker.view_progress(data)
        elif choice == "9":
            print_header("EXAM COUNTDOWN")
            tracker.view_countdown(data)
        elif choice == "10":
            print_header("DELETE TOPIC")
            tracker.delete_topic(data)
        elif choice == "11":
            print_header("DELETE SUBJECT")
            tracker.delete_subject(data)
        elif choice == "12":
            save_data(data)
            print("\nData saved. Good luck with your exams!")
            break

        # Save after every action so nothing is lost if the program closes.
        save_data(data)
        pause()


if __name__ == "__main__":
    main()