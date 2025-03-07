use std::{fs::{self, DirEntry, File}, io::{self, Read}, path::PathBuf};

pub fn list_removable_disks() -> io::Result<Vec<String>> {
    let mut devices: Vec<String> = vec!();

    for entry in fs::read_dir("/sys/block")? {
        let entry = entry?;
        if is_removable(&entry) && is_disk(&entry) {
            let name = entry.file_name();
            if let Some(device) = name.to_str() {
                devices.push(String::from(device));
            }
        }
    }

    Ok(devices)

}

fn check_first_byte(path: &PathBuf, value: u8) -> bool {
    let file = File::open(path);
    if let Ok(file) = file {
        let data = file.bytes().next();
        if let Some(Ok(data)) = data {
            return data == value;
        }
    }

    false

}

fn is_removable(entry: &DirEntry) -> bool {
    let mut path = entry.path();
    path.push("removable");

    check_first_byte(&path, b'1')
}

fn is_disk(entry: &DirEntry) -> bool {
    let mut path = entry.path();
    path.push("device");
    path.push("type");

    let scsi_type_disk = b'0';
    check_first_byte(&path, scsi_type_disk)
}