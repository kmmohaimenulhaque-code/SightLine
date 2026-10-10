import os
import subprocess

status = subprocess.check_output(['git', 'status', '--porcelain']).decode('utf-8').splitlines()

paths_to_process = []
for line in status:
    if len(line) > 3:
        state = line[:2]
        filepath = line[3:]
        if filepath.startswith('"') and filepath.endswith('"'):
            filepath = filepath[1:-1]
        paths_to_process.append((state, filepath))

files_to_rename = []

for state, filepath in paths_to_process:
    if os.path.isdir(filepath):
        for root, dirs, files in os.walk(filepath):
            for file in files:
                files_to_rename.append((state, os.path.join(root, file)))
    else:
        files_to_rename.append((state, filepath))

for state, filepath in files_to_rename:
    dir_name = os.path.dirname(filepath)
    base_name = os.path.basename(filepath)
    
    if base_name.startswith('3.1pro_'):
        continue
        
    new_base_name = f'3.1pro_{base_name}'
    new_filepath = os.path.join(dir_name, new_base_name)
    
    print(f"Renaming {filepath} -> {new_filepath}")
    os.rename(filepath, new_filepath)
    
    if 'M' in state or 'D' in state:
        subprocess.run(['git', 'rm', '--cached', filepath], check=False)

print(f"Processed {len(files_to_rename)} files.")
