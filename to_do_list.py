import tkinter as tk
from tkcalendar import Calendar
from datetime import date
import json
import os

class Task:
    """Represents a single task with UI elements and data management."""
    
    calendar_isopen = False  # Prevents multiple calendar windows from opening simultaneously

    def __init__(self, parent_frame, text, parent_tasks_list, app):
        """Initialize a Task object with UI elements."""

        self.parent_frame = parent_frame
        self.parent_tasks_list = parent_tasks_list
        self.app = app  # Reference to app for saving tasks
        self.text = text

        # Task state variables
        self.icon_index = 0  # Current urgency icon (0=not urgent, 1=neutral, 2=urgent)
        self.icons = ["😃", "😐", "😠"]  # Available urgency icons
        self.due_date = "Due Date"  # Default due date text
        self.is_checked = False  # Tracks if task is completed

        # Create main frame for this task
        self.frame = tk.Frame(self.parent_frame)
        self.frame.pack(anchor=tk.W, pady=5, padx=10)

        # Date button - allows user to set a due date using calendar
        self.date_btn = tk.Button(self.frame, text=self.due_date, font=("Tahoma", 18), command=self.open_calendar)
        self.date_btn.pack(padx=10, side=tk.LEFT)

        # Urgency icon button - cycles through different urgency icons
        self.icon_btn = tk.Button(self.frame, text=self.icons[self.icon_index], width=3, font=("Tahoma", 18), bg="#ff99a8", command=self.change_icon)
        self.icon_btn.pack(side=tk.LEFT)

        # Delete button - removes the task
        self.delete_btn = tk.Button(self.frame, text="    🗑️", width=3, font=("Tahoma", 18), bg="#ffc0cb", command=self.delete_self)
        self.delete_btn.pack(side=tk.LEFT, padx=5)

        # Check button - marks task as completed
        self.check_btn = tk.Button(self.frame, text="", width=3, font=("Tahoma", 18), bg="#ffccd5", command=self.toggle_check)
        self.check_btn.pack(side=tk.LEFT)

        # Task label - displays the task text
        self.label = tk.Label(self.frame, text=self.text, font=("Tahoma", 21))
        self.label.pack(padx=10, side=tk.LEFT)

    def change_icon(self):
        """Cycle through mood icons and save changes."""
        self.icon_index = (self.icon_index + 1) % len(self.icons)  # Move to next icon
        self.icon_btn.config(text=self.icons[self.icon_index])  # Update button display
        self.app.save_tasks()  # Persist change to JSON file

    def toggle_check(self):
        """Mark task as completed or incomplete, update visual appearance, and save."""
        self.is_checked = not self.is_checked
        if self.is_checked:
            text = "✔️"  # Show checkmark
            color = "grey"  # Gray out completed tasks
        else:
            text = ""  # Hide checkmark
            color = "black"  # Return to normal color
        self.check_btn.config(text=text)
        self.label.config(fg=color)  # Apply color change to task text
        self.app.save_tasks()  # Persist change to JSON file
        

    def delete_self(self):
        """Delete this task from the UI and task list, then save changes."""
        self.frame.destroy()  # Remove UI elements
        self.parent_tasks_list.remove(self)  # Remove from tasks list
        self.app.save_tasks()  # Persist change to JSON file

    def open_calendar(self):
        """Open a calendar window to allow the user to select a due date."""
        # Checks if there are other calendars window open
        if not Task.calendar_isopen:
            Task.calendar_isopen = True
            cal_window = tk.Toplevel(self.parent_frame)  # Create new window
            today = date.today()
            cal = Calendar(cal_window, selectmode='day', year=today.year, month=today.month, day=today.day)
            cal.pack(pady=20)

            # Function to close calendar without selecting a date
            def close_calendar():
                Task.calendar_isopen = False
                cal_window.destroy()          

            # Intercept the OS 'X' button to properly close calendar
            cal_window.protocol("WM_DELETE_WINDOW", close_calendar)

            # Function to set a date and close the calendar
            def set_date():
                Task.calendar_isopen = False
                self.due_date = cal.get_date()  # Get selected date from calendar
                self.date_btn.config(text=self.due_date)  # Update button text
                self.app.save_tasks()  # Persist change to JSON file
                cal_window.destroy()

            confirm_btn = tk.Button(cal_window, text="Confirm Date", command=set_date)
            confirm_btn.pack(pady=20)

# Whole App Class
class TodoApp:
    """Main application class that manages the task list UI and data persistence."""
    
    def __init__(self, root):
        """Initialize the TodoApp application"""
        
        self.root = root
        self.root.title("Task Manager")
        self.root.geometry("600x600")
        self.root.resizable(True, True)  # Allow window resizing

        self.tasks = []  # List to store all Task objects
        self.setup_ui()  # Build the user interface
        self.load_tasks()  # Load previously saved tasks from JSON file

    def setup_ui(self):
        """Build and layout all the graphic elements of the app."""
        # Title label
        self.label = tk.Label(self.root, text="New Task:", font=("Tahoma", 14))
        self.label.pack(pady=10)

        # Input field for new tasks
        self.entry = tk.Entry(self.root, width=40, font=("Tahoma", 14))
        self.entry.pack(pady=5)

        # Button to add new task
        self.add_btn = tk.Button(self.root, text="Add", command=self.add_task, font=("Tahoma", 14))
        self.add_btn.pack(pady=10)

        # Container frame for scrollable task list
        container_frame = tk.Frame(self.root, height=300)
        container_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Canvas - allows scrolling of task list
        my_canvas = tk.Canvas(container_frame)
        my_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        # Scrollbar - enables vertical scrolling
        my_scrollbar = tk.Scrollbar(container_frame, orient=tk.VERTICAL, command=my_canvas.yview)
        my_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx = 10, pady = 5)

        # Inner Frame - holds all task widgets
        self.tasks_frame = tk.Frame(my_canvas)
        my_canvas.create_window((0, 0), window=self.tasks_frame, anchor="nw")

        # Configure canvas scrolling
        my_canvas.configure(yscrollcommand=my_scrollbar.set)
        # Update scroll region when tasks frame changes size
        self.tasks_frame.bind('<Configure>', lambda e: my_canvas.configure(scrollregion=my_canvas.bbox("all")))

    def add_task(self):
        """Add a new task from the input field to the task list."""
        try:
            task_text = self.entry.get().strip()  # Get text from input field
            if task_text:  # Only add if text is not empty
                new_task = Task(self.tasks_frame, task_text, self.tasks, self)
                self.tasks.append(new_task)
                self.entry.delete(0, tk.END)  # Clear input field
                self.save_tasks()  # Save new task to JSON file
        except Exception as e:
            print(f"Error adding task: {e}")

    def save_tasks(self):
        """
        Save all tasks to a JSON file for persistent storage.
        
        The JSON file stores: task text, due date, completion status, and mood icon.
        """
        tasks_data = []
        # Convert each Task object to a dictionary
        for task in self.tasks:
            tasks_data.append({
                "text": task.text,
                "due_date": task.due_date,
                "is_checked": task.is_checked,
                "icon_index": task.icon_index
            })
        # Write data to tasks.json file
        with open("tasks.json", "w") as f:
            json.dump(tasks_data, f, indent=2)

    def load_tasks(self):
        """Load previously saved tasks from the JSON file and recreate them in the UI."""
        if os.path.exists("tasks.json"):
            try:
                # Read data from JSON file
                with open("tasks.json", "r") as f:
                    tasks_data = json.load(f)
                # Recreate each task from saved data
                for task_data in tasks_data:
                    new_task = Task(self.tasks_frame, task_data["text"], self.tasks, self)
                    # Restore task properties
                    new_task.due_date = task_data["due_date"]
                    new_task.is_checked = task_data["is_checked"]
                    new_task.icon_index = task_data["icon_index"]
                    
                    # Update UI to match saved state
                    new_task.date_btn.config(text=new_task.due_date)
                    new_task.icon_btn.config(text=new_task.icons[new_task.icon_index])
                    if new_task.is_checked:
                        new_task.check_btn.config(text="✔️")
                        new_task.label.config(fg="grey")  # Gray out completed tasks
                    self.tasks.append(new_task)
            except Exception as e:
                print(f"Error loading tasks: {e}")

if __name__ == "__main__":
    """Main entry point - create and run the application."""
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()