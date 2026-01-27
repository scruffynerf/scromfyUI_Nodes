import os
import importlib
import glob
import sys

# Mappings to be exported to ComfyUI
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

def load_nodes():
    # Get the path to the 'py' directory
    base_path = os.path.dirname(__file__)
    py_path = os.path.join(base_path, "py")
    
    if not os.path.exists(py_path):
        print(f"[scromfyUI] 'py' directory not found at {py_path}")
        return

    # Scan for .py files in the 'py' directory (top level only for nodes)
    # Support code should live in subdirectories
    files = glob.glob(os.path.join(py_path, "*.py"))
    
    # Ensure the 'py' directory is in the path for relative imports if needed
    # but since this is a package, we should use relative imports via f".py.{module_name}"
    
    loaded_count = 0
    modules_loaded = []
    
    for file in files:
        module_name = os.path.basename(file)[:-3]
        if module_name == "__init__":
            continue
            
        try:
            # Import the module. Since __init__.py is at the root of the custom_nodes/folder,
            # and 'py' is a subdirectory, we use .py.module_name
            module = importlib.import_module(f".py.{module_name}", package=__name__)
            
            # Collect mappings
            m_count = 0
            if hasattr(module, "NODE_CLASS_MAPPINGS"):
                new_nodes = module.NODE_CLASS_MAPPINGS
                NODE_CLASS_MAPPINGS.update(new_nodes)
                m_count = len(new_nodes)
            
            if hasattr(module, "NODE_DISPLAY_NAME_MAPPINGS"):
                NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)
            
            if m_count > 0:
                modules_loaded.append(f"{module_name} ({m_count})")
                loaded_count += m_count
                
        except Exception as e:
            print(f"[scromfyUI] Failed to load module {module_name}: {e}")

    if modules_loaded:
        print(f"[scromfyUI] Loaded modules: {', '.join(modules_loaded)}")
    print(f"[scromfyUI] Total nodes initialized: {loaded_count}")

# Perform the load
load_nodes()

# ComfyUI Web Directory
WEB_DIRECTORY = "./js"

# Cleanup to avoid polluting the namespace
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
