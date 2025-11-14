import bpy, sys, os, shutil, glob

print("Blender Python:", sys.executable)
print("Python version:", sys.version)

# Locate Blender's modules directory
user_scripts = bpy.utils.script_path_user() or bpy.utils.user_resource('SCRIPTS')
modules_dir = os.path.join(user_scripts, "modules")

print(f"Target modules dir: {modules_dir}")

if not os.path.exists(modules_dir):
    print("✓ Modules directory doesn't exist. Nothing to uninstall.")
    sys.exit(0)

# Find all zeroconf-related files/directories
patterns = [
    "zeroconf*",
    "ifaddr*",
    "async_timeout*",
]

removed = []
for pattern in patterns:
    matches = glob.glob(os.path.join(modules_dir, pattern))
    for path in matches:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
                removed.append(f"DIR: {path}")
            else:
                os.remove(path)
                removed.append(f"FILE: {path}")
        except Exception as e:
            print(f"✗ Failed to remove {path}: {e}")

if removed:
    print(f"\n✓ Removed {len(removed)} items:")
    for item in removed:
        print(f"  - {item}")
    print("\n✓ zeroconf uninstalled successfully!")
else:
    print("\n✓ No zeroconf files found. Already clean.")
