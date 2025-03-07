#!/usr/bin/env python3

from dataclasses import dataclass
import subprocess
import json
import os
import hashlib

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

CHUNK_SIZE = 100 * 1024

class WriteImageContext:
    device: str
    filename: str
    progressbar: None
    state: str
    error_message: str
    file_size: int
    remaining: int
    device_file: None
    image_file: None
    write_checksum: None
    check_checksum: None

    def __init__(self, ):
        self.progessbar = None
        self.state = "uninitialized"

    def reset(self, device, filename):
        self.device = device
        self.filename = filename
        self.error_message = None
        self.file_size = 0
        self.remaining = 0
        self.device_file = None
        self.image_file = None
        self.write_checksum = hashlib.sha256()
        self.check_checksum = hashlib.sha256()
        self.state = "init"

    def cleanup(self):
        if self.device_file is not None:
            self.device_file.close()
            self.device_file = None
        if self.image_file is not None:
            self.image_file.close()
            self.image_file = None
        self.state = "uninitialized"

    def next(self) -> bool:
        if self.state == "init":
            if not os.path.isfile(self.filename):
                self.error_message = "Image file not found"
                self.state = "error"
                return false
            if self.filename.endswith(".xz"):
                result = subprocess.run(["unxz", self.filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode != 0:
                    self.error_message = "Failed to decompress image"
                    self.state = "error"
                    return False
                self.filename = self.filename[:-3]
            self.file_size = os.path.getsize(self.filename)
            self.progressbar["maximum"] = self.file_size
            self.progressbar["value"] = 0
            self.remaining = self.file_size
            # umount 
            for file in os.listdir("/dev/"):
                if file.startswith(self.device) and len(file) > len(self.device):
                    result = subprocess.run(["umount", f"/dev/{file}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
                    if result.returncode != 0:
                        print(f"warn: failed to unmount /dev/{file}: {result.stderr.strip()}")
            self.device_file = open(f"/dev/{self.device}", "wb")
            self.image_file = open(self.filename, "rb")
            self.state = "write"
            return True
        elif self.state == "write":
            if self.remaining == 0:
                self.device_file.close()
                self.device_file = open(f"/dev/{self.device}", "rb")
                self.image_file.close()
                self.image_file = None
                self.remaining = self.file_size
                self.progressbar["value"] = 0
                self.state = "check"
                return True
            try:
                buffer = self.image_file.read(min(CHUNK_SIZE, self.remaining))
                if not buffer:
                    self.error_message = "Failed to read image"
                    self.state = "error"
                    return False
                self.remaining -= len(buffer)
                self.write_checksum.update(buffer)
                self.device_file.write(buffer)
                self.progressbar["value"] = (self.file_size - self.remaining) / 2
                return True
            except Exception as ex:
                self.error_message = f"Failed to write image: {ex}"
                self.state = "error"
                return False
        elif self.state == "check":
            if self.remaining == 0:
                if self.write_checksum.hexdigest() != self.check_checksum.hexdigest():
                    self.error_message = "Checksum error"
                    self.state = "error"
                    return False
                self.state = "done"
                return False
            try:
                buffer = self.device_file.read(min(CHUNK_SIZE, self.remaining))
                if not buffer:
                    self.error_message = "Failed to read image"
                    self.state = "error"
                    return False
                self.remaining -= len(buffer)
                self.check_checksum.update(buffer)
                self.progressbar["value"] = self.file_size - (self.remaining  / 2)
                return True
            except Exception as ex:
                self.error_message = f"Failed to read image: {ex}"
                self.state = "error"
                return False
        else:
            return False


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

def write_image_start(root, context, device, filename):
    context.reset(device, filename)
    root.event_generate("<<WriteImageNext>>", when="tail")
    
def write_image_next(root, context):
    if context.next():
        root.update()
        root.event_generate("<<WriteImageNext>>", when="tail")
    else:
        if context.state == "error":
            messagebox.showerror(title="Error", message=context.error_message)
        else:
            messagebox.showinfo(title="Completed", message="Image successfully flashed")
        context.cleanup()

def main():
    root = TkinterDnD.Tk()
    root.title("Write Image")
    root.resizable(height=False, width=False)

    filename = tk.StringVar()
    context = WriteImageContext()

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
    choose_file_button.grid(row=1, column=3, padx=5, pady=5, sticky=tk.EW)

    write_image_button = tk.Button(root, text="Write Image",
        command=lambda: write_image_start(root, context, device_name.get(), filename.get()))
    write_image_button.grid(row=2, column=3, padx=5, pady=5, sticky=tk.EW)

    progressbar = ttk.Progressbar()
    progressbar.grid(row=3,column=0, columnspan=4, padx=10, pady=10, sticky=tk.EW)

    context.progressbar = progressbar
    root.bind("<<WriteImageNext>>", lambda _: write_image_next(root, context))

    root.mainloop()

if __name__ == "__main__":
    main()
