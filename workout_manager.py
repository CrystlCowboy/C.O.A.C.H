import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import atexit

# Connect to the SQLite database and create tables
def connect_db():
    conn = sqlite3.connect('workout_logs.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS workout_logs (
                        id INTEGER PRIMARY KEY,
                        date TEXT NOT NULL,
                        workout_day_type TEXT NOT NULL
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS exercise_logs (
                        id INTEGER PRIMARY KEY,
                        workout_log_id INTEGER,
                        exercise TEXT NOT NULL,
                        FOREIGN KEY (workout_log_id) REFERENCES workout_logs(id)
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sets (
                        id INTEGER PRIMARY KEY,
                        exercise_log_id INTEGER,
                        set_number INTEGER,
                        reps INTEGER,
                        weight_used REAL,
                        FOREIGN KEY (exercise_log_id) REFERENCES exercise_logs(id)
                    )''')
    conn.commit()
    conn.close()

# Add a workout log with exercises and sets
def add_workout_log():
    date_str = date_entry.get()
    workout_day_type = workout_day_type_entry.get()
    exercise = exercise_entry.get()
    
    sets_data = []  # List to hold (reps, weight) tuples
    for entry in sets_frame.winfo_children():
        if isinstance(entry, ttk.Entry):
            sets_data.append(entry.get())

    if len(sets_data) % 2 != 0:
        messagebox.showerror("Error", "Please provide both reps and weight for each set.")
        return

    try:
        date_obj = datetime.strptime(date_str, '%m-%d-%Y')
        date_formatted = date_obj.strftime('%m-%d-%Y')
    except ValueError:
        messagebox.showerror("Error", "Invalid date format. Please use MM-DD-YYYY.")
        return

    if date_formatted and exercise and workout_day_type:
        conn = sqlite3.connect('workout_logs.db')
        cursor = conn.cursor()

        cursor.execute('INSERT INTO workout_logs (date, workout_day_type) VALUES (?, ?)',
                       (date_formatted, workout_day_type))
        workout_log_id = cursor.lastrowid  

        cursor.execute('INSERT INTO exercise_logs (workout_log_id, exercise) VALUES (?, ?)',
                       (workout_log_id, exercise))
        exercise_log_id = cursor.lastrowid

        for i in range(0, len(sets_data), 2):  
            set_reps = sets_data[i]
            set_weight = sets_data[i + 1]
            cursor.execute('INSERT INTO sets (exercise_log_id, set_number, reps, weight_used) VALUES (?, ?, ?, ?)',
                           (exercise_log_id, (i // 2) + 1, set_reps, set_weight))

        conn.commit()  
        conn.close()

        messagebox.showinfo("Success", "Workout log added!")
        clear_entries()
        fetch_workout_logs()
    else:
        messagebox.showerror("Error", "Please fill in all required fields.")

# Delete a workout log
def delete_workout_log():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Warning", "No item selected")
        return

    for item in selected_item:
        item_values = tree.item(item, "values")
        log_id = item_values[0]
        delete_log_from_db(log_id)
        tree.delete(item)

    messagebox.showinfo("Info", "Selected log(s) deleted successfully")

def delete_log_from_db(log_id):
    conn = sqlite3.connect('workout_logs.db')
    cursor = conn.cursor()

    # Delete from the "sets" table
    cursor.execute('''DELETE FROM sets 
                      WHERE exercise_log_id IN 
                        (SELECT id FROM exercise_logs WHERE workout_log_id = ?)''', (log_id,))
    
    # Delete from the "exercise_logs" table
    cursor.execute('DELETE FROM exercise_logs WHERE workout_log_id = ?', (log_id,))

    # Delete from the "workout_logs" table
    cursor.execute('DELETE FROM workout_logs WHERE id = ?', (log_id,))

    conn.commit()
    conn.close()

# Search logs
def search_logs():
    search_term = search_entry.get().lower()

    for row in tree.get_children():
        tree.delete(row)

    conn = sqlite3.connect('workout_logs.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT workout_logs.id, workout_logs.date, workout_logs.workout_day_type, exercise_logs.exercise, sets.set_number, sets.reps, sets.weight_used
                      FROM workout_logs
                      JOIN exercise_logs ON workout_logs.id = exercise_logs.workout_log_id
                      JOIN sets ON exercise_logs.id = sets.exercise_log_id
                      WHERE LOWER(workout_logs.date) LIKE ? OR LOWER(workout_logs.workout_day_type) LIKE ? OR LOWER(exercise_logs.exercise) LIKE ?''',
                   ('%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%'))
    logs = cursor.fetchall()
    conn.close()

    for log in logs:
        tree.insert('', tk.END, values=(log[0], log[1], log[2], log[3], log[4], log[5]))

# Fetch workout logs
def fetch_workout_logs():
    conn = sqlite3.connect('workout_logs.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT workout_logs.id, workout_logs.date, workout_logs.workout_day_type, exercise_logs.exercise, sets.set_number, sets.reps, sets.weight_used
                      FROM workout_logs
                      JOIN exercise_logs ON workout_logs.id = exercise_logs.workout_log_id
                      JOIN sets ON exercise_logs.id = sets.exercise_log_id
                      ORDER BY workout_logs.date DESC, workout_logs.workout_day_type, exercise_logs.exercise, sets.set_number''')
    logs = cursor.fetchall()
    conn.close()

    for row in tree.get_children():
        tree.delete(row)

    for log in logs:
        tree.insert('', tk.END, values=(log[0], log[1], log[2], log[3], log[4], log[5]))

# Clear input fields
def clear_entries():
    date_entry.delete(0, tk.END)
    workout_day_type_entry.delete(0, tk.END)
    exercise_entry.delete(0, tk.END)
    for entry in sets_frame.winfo_children():
        entry.destroy()  
    add_set_input()  

# Add more set input fields
def add_set_input():
    reps_entry = ttk.Entry(sets_frame)
    reps_entry.pack()
    reps_entry.insert(0, "Reps")
    reps_entry.bind("<FocusIn>", lambda event: reps_entry.delete(0, tk.END))  

    weight_entry = ttk.Entry(sets_frame)
    weight_entry.pack()
    weight_entry.insert(0, "Weight (lbs)")
    weight_entry.bind("<FocusIn>", lambda event: weight_entry.delete(0, tk.END))  

# GUI setup
root = tk.Tk()
root.title("Workout Log Manager")
root.geometry("800x600")

connect_db()

# Labels and input fields
tk.Label(root, text="Date (MM-DD-YYYY)").grid(row=0, column=0)
date_entry = tk.Entry(root)
date_entry.grid(row=0, column=1)
date_entry.insert(0, datetime.now().strftime('%m-%d-%Y'))

tk.Label(root, text="Workout Day Type (Push, Pull, Leg)").grid(row=1, column=0)
workout_day_type_entry = tk.Entry(root)
workout_day_type_entry.grid(row=1, column=1)

tk.Label(root, text="Exercise").grid(row=2, column=0)
exercise_entry = tk.Entry(root)
exercise_entry.grid(row=2, column=1)

sets_frame = tk.Frame(root)
sets_frame.grid(row=3, column=0, columnspan=2)
add_set_input()

add_set_button = tk.Button(root, text="Add More Sets", command=add_set_input)
add_set_button.grid(row=4, column=0, columnspan=2)

add_button = tk.Button(root, text="Add Workout Log", command=add_workout_log)
add_button.grid(row=5, column=0, columnspan=2)

# Search bar
tk.Label(root, text="Search Logs").grid(row=6, column=0)
search_entry = tk.Entry(root)
search_entry.grid(row=6, column=1)

search_button = tk.Button(root, text="Search", command=search_logs)
search_button.grid(row=6, column=2)

# Show All button
show_all_button = tk.Button(root, text="Show All", command=fetch_workout_logs)
show_all_button.grid(row=6, column=3)

# Logs table
columns = ("ID", "Date", "Workout Day Type", "Exercise", "Set Number", "Reps", "Weight Used")
tree = ttk.Treeview(root, columns=columns, show='headings')
tree.heading("ID", text="ID")
tree.heading("Date", text="Date")
tree.heading("Workout Day Type", text="Workout Day Type")
tree.heading("Exercise", text="Exercise")
tree.heading("Set Number", text="Set Number")
tree.heading("Reps", text="Reps")
tree.heading("Weight Used", text="Weight Used (lbs)")
tree.grid(row=7, column=0, columnspan=4, sticky="nsew")

delete_button = tk.Button(root, text="Delete Selected Log", command=delete_workout_log)
delete_button.grid(row=8, column=0, columnspan=4)

fetch_workout_logs()

root.mainloop()