import os
import sys
import shutil
import psutil
import logging

def setup_logging(log_file):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file)
        ]
    )

def check_disk_space(path):
    total, used, free = shutil.disk_usage(path)
    return free

def is_case_sensitive(path):
    temp_file = os.path.join(path, "tempfile.tmp")
    temp_file_upper = os.path.join(path, "TEMPFILE.TMP")
    try:
        with open(temp_file, "w") as f:
            f.write("test")
        if os.path.exists(temp_file_upper):
            return True
        return False
    finally:
        os.remove(temp_file)
        if os.path.exists(temp_file_upper):
            os.remove(temp_file_upper)

def create_symlink(src, dest):
    if os.path.exists(dest):
        os.remove(dest)
    os.symlink(src, dest)

def move_and_create_symlink(src_file, dest_file):
    try:
        shutil.move(src_file, dest_file)
        create_symlink(dest_file, src_file)
        logging.info(f"Moved '{src_file}' to the central repository.")
        logging.info(f"Created symlink in '{os.path.dirname(src_file)}' pointing to '{dest_file}'.")
        return True
    except Exception as e:
        logging.error(f"An error occurred while moving or creating symlink for '{src_file}': {str(e)}")
        return False

def delete_symlink_and_restore(src, dest):
    try:
        os.remove(src)
        if os.path.exists(dest):
            shutil.move(dest, src)
            logging.info(f"Reverted move of '{dest}'.")
    except Exception as e:
        logging.error(f"An error occurred while deleting symlink or reverting move for '{src}': {str(e)}")

def revert_changes(playlist_folder, central_repo):
    logging.info("Reverting changes...")
    for root, _, files in os.walk(playlist_folder):
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(central_repo, file)
            if os.path.islink(src_file):
                dest_file_actual = os.path.realpath(src_file)
                delete_symlink_and_restore(src_file, dest_file_actual)
            elif os.path.exists(dest_file):
                delete_symlink_and_restore(src_file, dest_file)

def process_playlist_files(playlist_folder, central_repo):
    moved_files = []
    file_creation_time = {}  # Dictionary to store file creation time
    for root, _, files in os.walk(playlist_folder):
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(central_repo, file)

            # Skip the log file if it exists in the playlist folder
            if os.path.basename(src_file) == "music_symlink_log.txt":
                continue

            file_creation_time[src_file] = os.path.getctime(src_file)

    # Sort the files by creation time in ascending order
    sorted_files = sorted(file_creation_time.items(), key=lambda x: x[1])

    for src_file, _ in sorted_files:
        dest_file = os.path.join(central_repo, os.path.basename(src_file))
        if move_and_create_symlink(src_file, dest_file):
            moved_files.append(src_file)
    return moved_files

def main():
    print("Enter the path for the main 'DATA Central' folder:", end=" ")
    central_repo = input().strip()

    print("Enter the path for the folder containing your playlists:", end=" ")
    playlist_folder = input().strip()

    if not os.path.exists(central_repo) or not os.path.isdir(central_repo):
        print(f"ERROR: The central repository folder '{central_repo}' does not exist or is not a valid directory.")
        sys.exit(1)

    if not os.path.exists(playlist_folder) or not os.path.isdir(playlist_folder):
        print(f"ERROR: The playlist folder '{playlist_folder}' does not exist or is not a valid directory.")
        sys.exit(1)

    try:
        central_repo = os.path.abspath(central_repo)
        playlist_folder = os.path.abspath(playlist_folder)

        if not is_case_sensitive(central_repo):
            print("WARNING: The central repository folder is not case-sensitive. This might cause issues with symlinks.")

        free_space = check_disk_space(central_repo)
        if free_space < psutil.virtual_memory().available:
            print("ERROR: Insufficient disk space in the central repository.")
            sys.exit(1)

        log_file = os.path.join(playlist_folder, "music_symlink_log.txt")
        setup_logging(log_file)

        moved_files = process_playlist_files(playlist_folder, central_repo)

        print("INFO: Script completed successfully!")

        if moved_files:
            print(f"\n{len(moved_files)} file(s) were moved to the central repository:")
            for file in moved_files:
                print(file)
            print("\nPlease check if your files are there in the central repository.")
            print("If something went wrong and you want to revert the changes, type 'X'.")
            user_input = input().strip().lower()
            if user_input == "x":
                revert_changes(playlist_folder, central_repo)
                print("Changes reverted. Your files are back to their original locations.")
    except KeyboardInterrupt:
        print("\nOperation aborted by the user. Reverting changes...")
        revert_changes(playlist_folder, central_repo)
        sys.exit(1)

if __name__ == "__main__":
    main()
