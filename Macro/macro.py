import tkinter as tk
from tkinter import ttk
import threading
import time
import os
import sys
import datetime
from pynput import keyboard
from pynput.keyboard import Controller

# Determine base path depending on if running as .exe or script
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.abspath(".")

LOG_FILE = os.path.join(base_path, "Macro", "logs.txt")

recording = False
playing = False
recorded_sequence = []
pressed_keys = {}
kb_controller = Controller()

def is_valid_key(key):
    try:
        return key.char.isalnum()
    except AttributeError:
        return False

def on_press(key):
    if recording and is_valid_key(key):
        if key not in pressed_keys:
            pressed_keys[key] = time.time()

def on_release(key):
    if recording and key in pressed_keys:
        start_time = pressed_keys.pop(key)
        duration = time.time() - start_time
        timestamp = datetime.datetime.fromtimestamp(start_time)
        recorded_sequence.append((key.char, duration, timestamp))
        update_sequence_display()

def start_recording():
    global recording, recorded_sequence, pressed_keys
    recorded_sequence = []
    pressed_keys = {}
    recording = True
    sequence_display.delete(1.0, tk.END)
    update_status("Recording...", "orange")

def stop_recording():
    global recording
    recording = False
    update_status("Recording stopped. Auto-saving...", "white")
    save_to_file()

def update_sequence_display():
    sequence_display.delete(1.0, tk.END)
    for key_char, duration, timestamp in recorded_sequence:
        time_str = timestamp.strftime("%d/%m/%Y %H:%M:%S")
        sequence_display.insert(tk.END, f"{time_str} {key_char} for {duration:.2f} sec\n")

def play_sequence(loop=False):
    global playing
    playing = True
    update_status("Playing...", "lightgreen")
    while playing:
        for key_char, duration, timestamp in recorded_sequence:
            if not playing:
                break
            try:
                kb_controller.press(key_char)
                time.sleep(duration)
                kb_controller.release(key_char)
            except:
                pass
        if not loop:
            break
    update_status("Playback stopped.", "white")

def run_once():
    if not recorded_sequence:
        update_status("No sequence recorded.", "red")
        return
    threading.Thread(target=play_sequence, daemon=True).start()

def run_loop():
    if not recorded_sequence:
        update_status("No sequence recorded.", "red")
        return
    threading.Thread(target=play_sequence, args=(True,), daemon=True).start()

def stop_playing():
    global playing
    playing = False

def save_to_file():
    try:
        os.makedirs(os.path.join(base_path, "Macro"), exist_ok=True)
        with open(LOG_FILE, "w") as f:
            for key_char, duration, timestamp in recorded_sequence:
                time_str = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                f.write(f"{time_str} {key_char} for {duration:.2f} sec\n")
        update_status("Saved to logs.txt", "lightgreen")
    except:
        update_status("Error saving file", "red")

def load_from_file():
    global recorded_sequence
    recorded_sequence = []
    if not os.path.exists(LOG_FILE):
        return
    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(' ')
                if len(parts) >= 4:
                    date_str = parts[0]
                    time_str = parts[1]
                    key_char = parts[2]
                    duration_str = parts[4]
                    timestamp_str = f"{date_str} {time_str}"
                    timestamp = datetime.datetime.strptime(timestamp_str, "%d/%m/%Y %H:%M:%S")
                    duration = float(duration_str)
                    recorded_sequence.append((key_char, duration, timestamp))
        update_sequence_display()
        update_status("Loaded from logs.txt", "lightgreen")
    except:
        update_status("Error loading file", "red")

def update_status(text, color):
    status_label.config(text=f"Status: {text}", foreground=color)

root = tk.Tk()
root.title("🎮 AFK Macro Recorder")
root.geometry("400x520")
root.resizable(False, False)
root.configure(bg="#222222")

style = ttk.Style()
style.theme_use("default")
style.configure("TButton",
    background="#444444",
    foreground="white",
    font=("Segoe UI", 10),
    padding=6)
style.map("TButton",
    background=[('active', '#666666')])

mainframe = ttk.Frame(root, padding="10")
mainframe.pack(fill=tk.BOTH, expand=True)

title = ttk.Label(mainframe, text="🕹️ Macro Recorder", font=("Segoe UI", 16, "bold"))
title.pack(pady=(10, 15))

buttons = [
    ("🎙️ Record Keystrokes", start_recording),
    ("⏹️ Stop Recording", stop_recording),
    ("▶️ Run Once", run_once),
    ("🔁 Run on Repeat", run_loop),
    ("❌ Stop Running", stop_playing),
]

for text, cmd in buttons:
    ttk.Button(mainframe, text=text, command=cmd).pack(pady=5, fill="x", padx=20)

status_label = ttk.Label(mainframe, text="Status: Ready", foreground="white", background="#222222", font=("Segoe UI", 10))
status_label.pack(pady=8)

ttk.Label(mainframe, text="Recorded Keys:", background="#222222", foreground="white", font=("Segoe UI", 10)).pack()

sequence_display = tk.Text(mainframe, height=10, width=45, bg="#1e1e1e", fg="white", font=("Consolas", 10), insertbackground="white")
sequence_display.pack(pady=5)

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

load_from_file()
root.mainloop()
