import psutil
import tkinter as tk
from tkinter import ttk  # Import ttk for themed widgets
from flask import Flask, jsonify, request
import concurrent.futures
import time
from tabulate import tabulate
from plyer import notification
import threading

app = Flask(__name__)
api_key = "your_api_key_here"

# Function to get application usage data
def get_app_usage(app_filter=None):
    data = []
    current_time = time.time()

    for process in psutil.process_iter(['pid', 'name', 'create_time']):
        try:
            # Extract process name and start time
            name = process.info['name']

            # Apply the filter if provided
            if app_filter and app_filter.lower() not in name.lower():
                continue

            start_time = process.info['create_time']

            # Convert start time to "hh:mm:ss" format
            start_time_formatted = time.strftime("%H:%M:%S", time.localtime(start_time))

            # Calculate time duration
            duration_seconds = current_time - start_time
            duration_formatted = time.strftime("%H:%M:%S", time.gmtime(duration_seconds))

            data.append({
                "Name": name,
                "Start Time": start_time_formatted,
                "Duration": duration_formatted,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return data

# Tkinter GUI
class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Running Application Usage Data")

        # Modern styling using ttk styles
        style = ttk.Style()
        style.theme_use("clam")  # Choose a theme (e.g., "clam", "alt", "default", "vista")

        self.label = ttk.Label(root, text="Running Application Usage Data", font=("Helvetica", 14))
        self.label.pack(pady=10)

        # Entry widget for filtering by application name
        self.filter_entry = ttk.Entry(root, width=30, font=("Helvetica", 12))
        self.filter_entry.pack(pady=5)

        self.update_button = ttk.Button(root, text="Update Data", command=self.update_data)
        self.update_button.pack(pady=10)

        # Entry widget for setting a reminder time in seconds
        self.reminder_entry = ttk.Entry(root, width=15, font=("Helvetica", 12))
        self.reminder_entry.pack(pady=5)

        self.reminder_button = ttk.Button(root, text="Set Reminder", command=self.set_reminder)
        self.reminder_button.pack(pady=10)

        # Treeview widget for displaying tabular data
        self.tree = ttk.Treeview(root, columns=("Name", "Start Time", "Duration"), show="headings")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Start Time", text="Start Time")
        self.tree.heading("Duration", text="Duration")
        self.tree.pack(pady=10)

        # Schedule auto-update every 1 minute
        self.root.after(60000, self.auto_update)

    def update_data(self):
        # Get the filter value from the Entry widget
        app_filter = self.filter_entry.get()

        # Get running application usage data based on the filter
        running_apps_data = get_app_usage(app_filter)

        # Clear existing data in the Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert new data into the Treeview
        for app_data in running_apps_data:
            self.tree.insert("", "end", values=(app_data["Name"], app_data["Start Time"], app_data["Duration"]))

    def auto_update(self):
        # Call the update_data method
        self.update_data()

        # Schedule the next auto-update after 1 minute
        self.root.after(60000, self.auto_update)

    def set_reminder(self):
        try:
            reminder_time_seconds = int(self.reminder_entry.get())
        except ValueError:
            tk.messagebox.showinfo("Reminder", "Invalid input. Please enter a valid number of seconds.")
            return

        if reminder_time_seconds <= 0:
            tk.messagebox.showinfo("Reminder", "Please enter a positive number of seconds.")
            return

        threading.Timer(reminder_time_seconds, self.show_reminder).start()

    def show_reminder(self):
        notification_title = "Take a Break"
        notification_message = "It's time to take a break! Stretch and relax."

        # Send desktop notification
        notification.notify(
            title=notification_title,
            message=notification_message,
            app_name="App Reminder",
        )

# Flask API
@app.route('/api/app-usage', methods=['GET'])
def api_app_usage():
    api_filter = request.args.get('filter', None)

    if request.headers.get('Api-Key') == api_key:
        usage_data = get_app_usage(api_filter)
        return jsonify({"data": usage_data})
    else:
        return jsonify({"error": "Invalid API key"}), 401

def run_flask():
    app.run(port=5000, debug=True)

if __name__ == "__main__":
    # Start the Tkinter GUI
    root = tk.Tk()
    gui = AppGUI(root)

    # Start the Flask API in a separate thread
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.submit(run_flask)

    root.mainloop()