import os
import sys
import shutil
import psutil
import logging

def check_disk_space(path):
    total, used, free = shutil.disk_usage(path)
    return free

def is_case_sensitive(path):
    # Check if the file system is case-sensitive
    temp_file = os.path.join(path, "tempfile.tmp")
    temp_file_upper = os.path.join(path, "TEMPFILE.TMP")
    try:
        # Create a temporary file with lowercase name
        with open(temp_file, "w") as f:
            f.write("test")
        # Check if the uppercase version of the file exists
        if os.path.exists(temp_file_upper):
            return True
        return False
    finally:
        # Cleanup the temporary files
        os.remove(temp_file)
        if os.path.exists(temp_file_upper):
            os.remove(temp_file_upper)

def create_symlink(src, dest):
    # Remove the existing symlink if present
    if os.path.exists(dest):
        os.remove(dest)
    # Create the symlink
    os.symlink(src, dest)

def move_and_create_symlink(src_file, dest_file):
    try:
        # Move the file to the central repository
        shutil.move(src_file, dest_file)
        # Create a symlink from the central repository back to the original location
        create_symlink(dest_file, src_file)
        logging.info(f"Moved '{src_file}' to the central repository.")
        logging.info(f"Created symlink in '{os.path.dirname(src_file)}' pointing to '{dest_file}'.")
        return True
    except Exception as e:
        logging.error(f"An error occurred while moving or creating symlink for '{src_file}': {str(e)}")
        return False

def delete_symlink_and_restore(src, dest):
    try:
        # Delete the symlink
        os.remove(src)
        # If the destination file exists, it means it was moved; revert the move
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
            # Check if the file is a symlink and has been moved; revert the changes
            if os.path.islink(src_file):
                dest_file_actual = os.path.realpath(src_file)
                delete_symlink_and_restore(src_file, dest_file_actual)
            # If the destination file exists, it means it was moved; revert the move
            elif os.path.exists(dest_file):
                delete_symlink_and_restore(src_file, dest_file)

def process_playlist_files(playlist_folder, central_repo):
    # Store the list of moved files
    moved_files = []
    for root, _, files in os.walk(playlist_folder):
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(central_repo, file)
            # Move and create symlink for each file
            if move_and_create_symlink(src_file, dest_file):
                moved_files.append(src_file)
    return moved_files

def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
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

        # Check if the file system is case-sensitive
        if not is_case_sensitive(central_repo):
            print("WARNING: The central repository folder is not case-sensitive. This might cause issues with symlinks.")

        # Check if there is sufficient disk space in the central repository
        free_space = check_disk_space(central_repo)
        if free_space < psutil.virtual_memory().available:
            print("ERROR: Insufficient disk space in the central repository.")
            sys.exit(1)

        # Process the playlist files and get the list of moved files
        moved_files = process_playlist_files(playlist_folder, central_repo)

        print("INFO: Script completed successfully!")

        # If any files were moved, print the list of moved files for user verification
        if moved_files:
            print(f"\n{len(moved_files)} file(s) were moved to the central repository:")
            for file in moved_files:
                print(file)
            print("\nPlease check if your files are there in the central repository.")
            print("If something went wrong and you want to revert the changes, type 'X'.")
            user_input = input().strip().lower()
            if user_input == "x":
                # Revert the changes if the user chooses to do so
                revert_changes(playlist_folder, central_repo)
                print("Changes reverted. Your files are back to their original locations.")
    except KeyboardInterrupt:
        print("\nOperation aborted by the user. Reverting changes...")
        # Revert the changes if the script execution is interrupted
        revert_changes(playlist_folder, central_repo)
        sys.exit(1)

if __name__ == "__main__":
    main()