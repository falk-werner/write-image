#!/usr/bin/env python3

from dataclasses import dataclass
import subprocess
import json

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

def list_removable_devices():
    result = subprocess.run(["lsblk", "-a", "--json"],
        check=True, stdout=subprocess.PIPE, text=True)
    data = json.loads(result.stdout)

    removable_devices = []
    for info in data["blockdevices"]:
        is_removable = info["rm"]
        device_type = info["type"]
        if is_removable and device_type == "disk":
            name = info["name"]
            removable_devices.append(name)
    
    return removable_devices

def choose_file(filename):
    name = filedialog.askopenfilename()
    if name:
        filename.set(name)

def update_devices(device_chooser):
    devices = list_removable_devices()
    if len(devices) == 0:
        devices.append('--')
    device_chooser['values'] = devices
    device_chooser.current(0)

def write_image(device, filename):
    messagebox.showerror(title="Error", message="Not implemented.")

def main():
    root = TkinterDnD.Tk()
    root.title("Write Image")
    root.resizable(height=False, width=False)

    filename = tk.StringVar()

    logo = tk.PhotoImage(file="logo.png").subsample(3,3)
    drop_area = tk.Label(root, image=logo, relief=tk.RAISED)
    drop_area.grid(row=0, column=0, rowspan=3, padx=10, pady=10, sticky=tk.NSEW)
    drop_area.drop_target_register(DND_FILES)
    drop_area.dnd_bind('<<Drop>>', lambda event:
        filename.set(event.data))

    device_label = tk.Label(root, text="Device:")
    device_label.grid(row=0,column=1,padx=5,pady=5,sticky=tk.EW)

    device_name = tk.StringVar()
    device_chooser = ttk.Combobox(root, textvariable=device_name)
    device_chooser.grid(row=0,column=2,padx=5,pady=5,sticky=tk.EW)
    update_devices(device_chooser)

    update_button = tk.Button(root, text="Update",
        command=lambda: update_devices(device_chooser))
    update_button.grid(row=0, column=3, padx=5, pady=5, stick=tk.EW)

    image_label = tk.Label(root, text="Image:")
    image_label.grid(row=1, column=1, padx=5, pady=5,sticky=tk.EW)

    filename_entry = tk.Entry(root, textvar=filename)
    filename_entry.grid(row=1,column=2,padx=5,pady=5,sticky=tk.EW)
    filename_entry.drop_target_register(DND_FILES)
    filename_entry.dnd_bind('<<Drop>>', lambda event: 
        filename.set(event.data))

    choose_file_button = tk.Button(root, text="Choose File...",
        command=lambda: choose_file(filename))
    choose_file_button.grid(row=1, column=3, padx=5, pady=5, stick=tk.EW)

    write_image_button = tk.Button(root, text="Write Image",
        command=lambda: write_image(device_name.get(), filename.get()))
    write_image_button.grid(row=2, column=3, padx=5, pady=5, stick=tk.EW)

    root.mainloop()

if __name__ == "__main__":
    main()
