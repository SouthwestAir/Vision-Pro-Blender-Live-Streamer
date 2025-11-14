import bpy, sys, os, subprocess, ensurepip, importlib

print("Blender Python:", sys.executable)
print("Python version:", sys.version)

# Check if zeroconf already exists
try:
    zeroconf = importlib.import_module("zeroconf")
    print("✓ zeroconf already installed at:", zeroconf.__file__)
    try:
        import importlib.metadata as im
        print("✓ zeroconf version:", im.version("zeroconf"))
    except Exception:
        pass
    print("\nNo installation needed. Script complete.")
    sys.exit(0)
except ImportError:
    print("zeroconf not found. Proceeding with installation...\n")

# 1) Compute writable folder Blender auto-loads
user_scripts = bpy.utils.script_path_user() or bpy.utils.user_resource('SCRIPTS')
modules_dir = os.path.join(user_scripts, "modules")
os.makedirs(modules_dir, exist_ok=True)
print("Target modules dir:", modules_dir)

# 2) Ensure folder is on sys.path
if modules_dir not in sys.path:
    sys.path.append(modules_dir)

# 3) Ensure pip is available
try:
    ensurepip.bootstrap()
except Exception as e:
    print(f"Warning: ensurepip failed ({e}). Assuming pip already exists.")

try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
except subprocess.CalledProcessError as e:
    print(f"Warning: pip upgrade failed. Continuing anyway...")

# 4) Install zeroconf
print("\nInstalling zeroconf...")
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "--target", modules_dir, "zeroconf"])
    print("✓ Installation complete")
except subprocess.CalledProcessError as e:
    print(f"\n✗ ERROR: Failed to install zeroconf.")
    print(f"  Try manually running: {sys.executable} -m pip install --target {modules_dir} zeroconf")
    sys.exit(1)

# 5) Verify import
try:
    zeroconf = importlib.import_module("zeroconf")
    print("✓ zeroconf loaded from:", zeroconf.__file__)
except ModuleNotFoundError as e:
    print("\nImport failed, checking pip location...")
    try:
        out = subprocess.check_output([sys.executable, "-m", "pip", "show", "-f", "zeroconf"], text=True)
        loc_line = next((line for line in out.splitlines() if line.lower().startswith("location:")), None)
        if loc_line:
            loc = loc_line.split(":", 1)[1].strip()
            if loc and loc not in sys.path:
                sys.path.append(loc)
                print("Added to sys.path:", loc)
        zeroconf = importlib.import_module("zeroconf")
        print("✓ zeroconf loaded after path fix:", zeroconf.__file__)
    except Exception as e2:
        print(f"\n✗ ERROR: Cannot import zeroconf after installation.")
        print(f"  Error: {repr(e2)}")
        print(f"\n  Please restart Blender and try enabling the Vision Pro Streamer add-on.")
        sys.exit(1)

# Show version
try:
    import importlib.metadata as im
    print("✓ zeroconf version:", im.version("zeroconf"))
except Exception:
    pass

print("\n✓ SUCCESS: zeroconf is ready to use!")
