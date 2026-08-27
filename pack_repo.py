import os

# Set the path to your target directory
# Use '.' for current folder, or specify: r"C:\path\to\your\folder"
TARGET_DIR = "."

# File extensions to include (add or remove as needed)
ALLOWED_EXTS = {".py", ".md", ".json", ".txt", ".yaml", ".yml", ".sql"}

# Folders to completely ignore
IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", "build", "dist", ".idea", ".vscode"}

OUTPUT_FILE = "combined_repository.txt"


def pack_folder(target_dir, output_file):
    with open(output_file, "w", encoding="utf-8") as outfile:
        for root, dirs, files in os.walk(target_dir):
            # Exclude unwanted directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in ALLOWED_EXTS and file != output_file and file != "pack_repo.py":
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, target_dir)

                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as infile:
                            outfile.write(f"\n{'=' * 50}\n")
                            outfile.write(f"FILE: {rel_path}\n")
                            outfile.write(f"{'=' * 50}\n\n")
                            outfile.write(infile.read())
                            outfile.write("\n\n")
                    except Exception as e:
                        print(f"Skipping {rel_path}: {e}")

    print(f"Done! Combined file saved as: {output_file}")


if __name__ == "__main__":
    pack_folder(TARGET_DIR, OUTPUT_FILE)