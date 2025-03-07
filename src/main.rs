use fltk::{app, enums::{Color, Event, FrameType}, frame::Frame, group::Grid, image::PngImage, menu::Choice, misc::Progress, prelude::{ GroupExt, MenuExt, WidgetBase, WidgetExt}, window::Window};

const WIDTH: i32 =640;
const HEIGHT: i32 =180;

fn main() {
    let screen = app::Screen::new(0)
        .expect("Failed to find default screen.");

    let app = app::App::default();
    let mut window = Window::default()
        .with_label("Write Image")
        .with_size(WIDTH, HEIGHT)
        .with_pos( (screen.w() - WIDTH) / 2,  (screen.h() - HEIGHT) / 2);

    let mut grid = Grid::default_fill();
    grid.set_layout(4, 5);
    grid.set_margin(10, 10, 10, 10);
    grid.set_gap(5, 5);
    //grid.show_grid(true);


    let image = PngImage::from_data(include_bytes!("logo.png")).unwrap();
    let mut label = Frame::default();
    label.set_size(100, 100);
    label.set_frame(FrameType::EngravedBox);
    grid.set_widget(&mut label, 0..3,0).unwrap();
    label.set_image_scaled(Some(image));

    let mut combo = Choice::default()
        .with_label("Device:")
        .with_size(10, 10);
    combo.add_choice("foo");
    combo.add_choice("bar");
    combo.set_value(0);
    
    grid.set_widget(&mut combo, 0, 2..4).unwrap();

    let mut progress_bar = Progress::default();
    progress_bar.set_maximum(100.0);
    progress_bar.set_value(35.0);
    progress_bar.set_color(Color::BackGround2);
    progress_bar.set_selection_color(Color::Selection);
    grid.set_widget(&mut progress_bar, 3, 0..5).unwrap();

    label.handle({
        let mut released = false;
        move |_, event| {
            match event {
                Event::DndEnter => {
                    released = false;
                    true
                }
                Event::DndDrag => {
                    true
                }
                Event::DndRelease => {
                    released = true;
                    true
                }
                Event::Paste => {
                    if released {
                        released = false;
                        println!("drop: {}", app::event_text());
                        true
                    }
                    else {
                        false
                    }
                }
                Event::Leave => {
                    released = false;
                    true
                }
                _ => false,
            }
        }
    });


    window.end();
    window.show();

    app.run().unwrap();
}
