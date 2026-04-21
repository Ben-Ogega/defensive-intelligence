import os 
import shutil

# ======================================================
# This script is used to rename files in a directory based on a specific pattern.
# Author: Ben Ogega
# Date: 2024-04-21
# Purpose: To automate the renaming of files in a directory by file type and a sequential number.
# ======================================================

'''
  ---- More than a label or a string of text, ----
More than a label or a string of text,
A file is defined by the life in its name;
A beacon that signals what follows it next,
Igniting the value and stoking the flame.

It acts as the key to a door once concealed,
A symbol of purpose, of essence, and soul;
In every clear title, a story's revealed,
The part of its being that makes the data whole.
'''
# Step 1 — Define the mapping of file extensions to folders
FOLDER_MAP = {
    #Documents
    '.pdf' : 'docs/references',
    '.docx' : 'docs/drafts',
    '.doc' : 'docs/drafts',
    '.txt' : 'docs/notes',
    '.xlsx' : 'docs/spreadsheets',
    '.pptx' : 'docs/presentations',
    '.ppt' : 'docs/presentations',
    '.csv' : 'data',
    '.json' : 'data',
    '.xml' : 'data',    
    '.md' : 'docs/markdown',
    '.rst' : 'docs/restructuredtext',
    '.yml' : 'docs/configurations',
    '.yaml' : 'docs/configurations',
    '.ini' : 'docs/configurations',
    '.log' : 'logs',
    '.cfg' : 'docs/configurations',
    '.conf' : 'docs/configurations',
    '.env' : 'docs/configurations',
    # Code files
    '.py' : 'code/python',
    '.js' : 'code/javascript',
    '.java' : 'code/java',
    '.cpp' : 'code/cpp',
    '.c' : 'code/c',
    '.ipynb' : 'code/notebooks',
    '.html' : 'code/web',
    '.css' : 'code/web',
    '.rb' : 'code/ruby',
    '.go' : 'code/go',
    '.rs' : 'code/rust',
    '.swift' : 'code/swift',
    '.cpp' : 'code/cpp',
    '.cs' : 'code/csharp',
    '.php' : 'code/php',
    '.sql' : 'code/sql',
    '.for' : 'code/fortran',
    '.has' : 'code/haskell',
    # Media files
    '.jpg' : 'figures',
    '.jpeg' : 'figures',
    '.png' : 'figures',
    '.gif' : 'figures',
    '.mp4' : 'media/videos',
    '.avi' : 'media/videos',
    '.mkv' : 'media/videos',
    '.mp3' : 'media/audio',
    '.wav' : 'media/audio',
    '.flac' : 'media/audio',
    '.ogg' : 'media/audio',
    # Archives
    '.zip' : 'archives',
    '.tar' : 'archives',
    '.gz' : 'archives',
    '.rar' : 'archives',
    '.7z' : 'archives',
    # Executables
    '.exe' : 'installers',
    '.msi' : 'installers',
    '.sh' : 'scripts',
    '.bat' : 'scripts',
    '.ps1' : 'scripts',
}

# Step 2 — Define the function to organize the folder
def organize_folder(folder_path):
    """
    Scans a folder and moves files into
    subfolders based on their extension.
    """
    # Track what we move
    moved = 0
    skipped = 0
    summary = {}

    # Step 2a — Get all files in the folder
   
    all_files = os.listdir(folder_path)


    for filename in all_files:

        # Step 2b — Build full file path
        try:
            file_path = os.path.join(folder_path, filename)
        except OSError as e:
            print(f"Error building file path for {filename}: {e}")
            skipped += 1
            continue

        # Step 2c — Skip folders, only process files
        try:
            if not os.path.isfile(file_path):
                skipped += 1
                continue
        except OSError as e:
            print(f"Error checking file type for {filename}: {e}")
            skipped += 1
            continue

        # Step 2d — Get file extension
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        # Step 2e — Find destination folder
        if ext in FOLDER_MAP:
            destination_folder = os.path.join(
                folder_path,
                FOLDER_MAP[ext]
            )
        else:
            destination_folder = os.path.join(
                folder_path,
                'misc'
            )

        # Step 2f — Create destination if needed
        os.makedirs(destination_folder, exist_ok=True)

        # Step 2g — Move the file
        shutil.move(file_path,
                   os.path.join(destination_folder, filename))

        # Step 2h — Track summary
        category = FOLDER_MAP.get(ext, 'misc')
        summary[category] = summary.get(category, 0) + 1
        moved += 1

    return moved, skipped, summary

def get_folder_from_user():
    """
    Asks the user which folder to organize.
    Returns the folder path.
    """
    print("\n" + "="*50)
    print("   Safari-Safe-AI | File Organizer")
    print("   Author: Ben Ogega | BRIDGE Framework")
    print("="*50)
    print("\nWhich folder would you like to organize?")
    print("1. Downloads")
    print("2. Desktop")
    print("3. Enter custom path")
    print("4. Exit")

    choice = input("\nEnter your choice (1-4): ").strip()

    if choice == "1":
        return os.path.join(os.path.expanduser("~"),
                           "Downloads")
    elif choice == "2":
        return os.path.join(os.path.expanduser("~"),
                           "Desktop")
    elif choice == "3":
        custom = input("Enter full folder path: ").strip()
        return custom
    elif choice == "4":
        print("Goodbye.")
        return None
    else:
        print("Invalid choice. Please try again.")
        return get_folder_from_user()


def print_summary(moved, skipped, summary):
    """
    Prints a clean summary of what was organized.
    """
    print("\n" + "="*50)
    print("   ORGANIZATION COMPLETE")
    print("="*50)
    print(f"\n✅ Files moved:   {moved}")
    print(f"⏭️  Items skipped: {skipped}")
    print("\n📁 Breakdown by category:")
    for category, count in sorted(summary.items()):
        print(f"   {category:<25} {count} file(s)")
    print("="*50)


# ============================================
# MAIN — Entry point
# ============================================
if __name__ == "__main__":
    folder = get_folder_from_user()

    if folder:
        if not os.path.exists(folder):
            print(f"\n❌ Folder not found: {folder}")
        else:
            print(f"\n🔍 Scanning: {folder}")
            moved, skipped, summary = organize_folder(folder)
            print_summary(moved, skipped, summary)
