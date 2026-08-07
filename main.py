from config import FILE_LIST_PATH
from src.notify import send_detection
from src.plot_event import plot_event
from src.run_EQNet import run_EQNet
from src.utils import (
    build_file_list,
    delete_old_empty_pick_files,
    get_last_pick_file,
    get_new_pick_files,
)

if __name__ == "__main__":
    last_pick_file = get_last_pick_file()
    print(f"Last pick file: {last_pick_file}")
    num_files = build_file_list(last_pick_file=last_pick_file)
    print(f"Built file list with {num_files} files")

    print("Running EQNet...")
    run_EQNet(file_list=FILE_LIST_PATH)

    new_pick_files = get_new_pick_files(last_pick_file=last_pick_file)
    print(f"Found {len(new_pick_files)} new pick files to plot")

    for pick_file in new_pick_files:
        try:
            event = plot_event(pick_file)
            print(f"Saved plot: {event.image_path}")
            send_detection(
                image_path=event.image_path,
                num_picks=event.num_picks,
                event_time=event.event_time,
            )
        except Exception as error:
            print(f"Failed to process {pick_file.name}: {error}")

    num_deleted = delete_old_empty_pick_files(last_pick_file=last_pick_file)
    print(f"Deleted {num_deleted} old empty pick files")
