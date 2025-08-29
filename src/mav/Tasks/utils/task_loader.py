import pkgutil
import importlib
import inspect
import os

def load_attack_tasks(file_path: str, package: str):
    # Path to the current package directory
    current_dir = os.path.join(file_path,"attack_tasks")
    # print("current_dir", current_dir)
    # print(list(pkgutil.iter_modules([current_dir])))

    for _, module_name, is_pkg in pkgutil.iter_modules([current_dir]):
        # print(module_name, is_pkg)
        if is_pkg:
            continue
        full_module_name = f"{package}.{module_name}"
        try:
            module = importlib.import_module(full_module_name)
        except Exception as e:
            print(e)
            continue  # Skip broken modules