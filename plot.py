from src.notify import send_detection
from src.plot_event import plot_event
from src.utils import (
    get_new_pick_files,
)

new_pick_files = get_new_pick_files()
print(f"Found {len(new_pick_files)} new pick files to plot")

for pick_file in new_pick_files:
    try:
        event = plot_event(pick_file, channel_start=300)
        print(f"Saved plot: {event.image_path}")
        send_detection(
            image_path=event.image_path,
            num_picks=event.num_picks,
            event_time=event.event_time,
        )
    except Exception as error:
        print(f"Failed to process {pick_file.name}: {error}")
