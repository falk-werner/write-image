use std::{cell::RefCell, io, rc::Rc};

use fltk::{app, button::Button, dialog::{FileChooser, FileChooserType}, enums::{Color, Event, FrameType}, frame::Frame, group::Grid, image::PngImage, input::Input, menu::Choice, misc::Progress, prelude::{ GroupExt, InputExt, MenuExt, WidgetBase, WidgetExt}, window::Window};

const WIDTH: i32 =640;
const HEIGHT: i32 =200;

const FILTER_ID_NONE: i32 = 0;
const FILTER_ID_XZ: i32 = 1;

mod device;
use crate::device::list_removable_disks;

struct Context
{
    device_chooser: Choice,
    image_input : Input,
    filter_chooser: Choice,
}

fn main() -> io::Result<()> {
    let screen = app::Screen::new(0)
        .expect("Failed to find default screen.");

    let app = app::App::default();
    let mut window = Window::default()
        .with_label("Write Image")
        .with_size(WIDTH, HEIGHT)
        .with_pos( (screen.w() - WIDTH) / 2,  (screen.h() - HEIGHT) / 2);

    let mut grid = Grid::default_fill();
    grid.set_layout(6, 5);
    grid.set_margin(10, 10, 10, 10);
    grid.set_gap(5, 5);

    let image = PngImage::from_data(include_bytes!("logo.png")).unwrap();
    let mut image_drop = Frame::default();
    image_drop.set_size(96, 96);
    image_drop.set_frame(FrameType::EngravedBox);
    image_drop.set_image_scaled(Some(image));
    grid.set_widget(&mut image_drop, 0..4,0).unwrap();

    let mut device_label = Frame::default().with_label("Device:");
    grid.set_widget(&mut device_label, 0, 1).unwrap();

    let mut device_chooser = Choice::default();
    grid.set_widget(&mut device_chooser, 0, 2..4).unwrap();

    let mut device_update = Button::default().with_label("Update");
    grid.set_widget(&mut device_update, 0, 4).unwrap();

    let mut image_label = Frame::default().with_label("Image:");
    grid.set_widget(&mut image_label, 1, 1).unwrap();

    let mut image_input = Input::default();
    grid.set_widget(&mut image_input, 1, 2..4).unwrap();

    let mut image_select = Button::default().with_label("Select");
    grid.set_widget(&mut image_select, 1, 4).unwrap();

    let mut filter_label = Frame::default().with_label("Filter:");
    grid.set_widget(&mut filter_label, 2, 1).unwrap();

    let mut filter_chooser = Choice::default();
    filter_chooser.add_choice("None");
    filter_chooser.add_choice("XZ");
    filter_chooser.set_value(0);
    grid.set_widget(&mut filter_chooser, 2, 2..4).unwrap();

    let mut begin_write = Button::default().with_label("Write");
    begin_write.take_focus().unwrap();
    grid.set_widget(&mut begin_write, 3, 4).unwrap();

    let mut progress_bar = Progress::default();
    progress_bar.set_color(Color::BackGround2);
    progress_bar.set_selection_color(Color::Selection);
    grid.set_widget(&mut progress_bar, 5, 0..5).unwrap();

    window.end();
    window.show();

    // ---

    let context = Context {
        device_chooser,
        image_input,
        filter_chooser
    };
    let context = Rc::new(RefCell::new(context));

    update_devices(&mut context.borrow_mut().device_chooser);
    device_update.set_callback({
        let context = context.clone();
        move |_| {            
            let mut ctx = context.borrow_mut();
            update_devices(&mut ctx.device_chooser);
        }
    });

    image_drop.handle({
        let mut released = false;
        let context = context.clone();
        move |_, event| {
            let mut ctx = context.borrow_mut();
            handle_image_drop(event, &mut released, &mut ctx)
        }
    });

    context.borrow_mut().image_input.handle({
        let mut released = false;
        let context = context.clone();
        move |_, event| {
            let mut ctx = context.borrow_mut();
            handle_image_drop(event, &mut released, &mut ctx)
        }
    });

    image_select.set_callback({
        let context = context.clone();
        move |_| {
            let  mut filechooser = FileChooser::new(".", "*.*", FileChooserType::Single, "Select File");
            filechooser.set_preview(false);
            filechooser.show();
            while filechooser.shown() {
                app::wait();
            }
            if let Some(filename) = filechooser.value(1) {
                let mut ctx = context.borrow_mut();
                ctx.image_input.set_value(filename.as_str());
                let filter = autodetect_filter(filename.as_str());
                ctx.filter_chooser.set_value(filter);
            }            
        }
    });


    app.run().unwrap();
    Ok(())
}

fn update_devices(device_chooser: &mut Choice) {
    device_chooser.clear();

    let devices = list_removable_disks();
    if let Ok(devices) = &devices {
        for device in devices {
            device_chooser.add_choice(device.as_str());
        }
        if devices.is_empty() {
            device_chooser.add_choice("-");
        }
    }
    else {
        device_chooser.add_choice("-");
    }

    device_chooser.set_value(0);
}

fn autodetect_filter(filename: &str) -> i32 {
    if filename.ends_with(".xz") { 
        FILTER_ID_XZ
    }  else {
        FILTER_ID_NONE
    }
}

fn handle_image_drop(event: Event, released: &mut bool, context: &mut Context) -> bool {
    match event {
        Event::DndEnter => {
            *released = false;
            true
        }
        Event::DndDrag => {
            true
        }
        Event::DndRelease => {
            *released = true;
            true
        }
        Event::Paste => {
            if *released {
                *released = false;
                let filename = app::event_text();
                context.image_input.set_value(filename.as_str());
                let filter = autodetect_filter(filename.as_str());
                context.filter_chooser.set_value(filter);
                true
            }
            else {
                false
            }
        }
        Event::DndLeave => {
//            *released = false;
            true
        }
        _ => false,
    }

}