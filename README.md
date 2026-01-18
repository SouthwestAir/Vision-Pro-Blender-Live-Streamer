# **Vision Pro Blender Live Streamer**

## **Overview**

The **Vision Pro Blender Live Streamer** is a two-part open-source project that enables real-time streaming of Blender scenes to Apple Vision Pro for immersive spatial preview. Create and edit in Blender, see results instantly in your Vision Pro.

This project consists of:

1. **Blender Add-on (Python):** Handles Bonjour/Zeroconf discovery, TCP connection, and real-time USDZ export
2. **Vision Pro Application (Swift/RealityKit):** Advertises via Bonjour, receives USDZ data, and renders in immersive space

## **Features**

- **Automatic Discovery:** Finds Vision Pro devices on your local network via Bonjour/Zeroconf
- **One-Click Installation:** Auto-installs required dependencies (python-zeroconf) from within Blender
- **Activity-Based Streaming:** Streams only when you're actively editing, pauses during idle periods to save resources
- **Real-time USDZ Export:** Exports scenes with materials, textures, and geometry optimized for Apple platforms
- **Configurable Frame Rate:** Control streaming speed (1-60 FPS)
- **Immersive Mixed Reality:** Renders scenes in Vision Pro's mixed immersion mode

## **Requirements**

- **Blender:** 5.0.0 or newer
- **Apple Vision Pro:** visionOS 1.0 or later
- **Network:** Both devices on the same local network (Wi-Fi)
- **Python Library:** python-zeroconf (auto-installed by add-on)

## **Installation**

### **1. Blender Add-on Setup**

#### **Quick Install (Recommended)**

1. **Download** the `Blender` folder containing:

   - `vision_pro_streamer_zeroconf.py` (main add-on)
   - `Utilities/auto_install_zeroconf.py` (optional dependency installer)
   - `Utilities/uninstall_zeroconf.py` (optional dependency remover)

2. **Install the add-on:**

   - Open Blender
   - Go to Edit > Preferences > Add-ons
   - Click "Install..." and select `vision_pro_streamer_zeroconf.py`
   - Enable the add-on: **"Development: Vision Pro Streamer (Zeroconf)"**

3. **Auto-install dependencies:**

   - The add-on will attempt to auto-install `python-zeroconf` on first use
   - If auto-install fails, run `Utilities/auto_install_zeroconf.py` with Blender's Python:

     - **Option A:** Open Blender's Scripting workspace, open `Utilities/auto_install_zeroconf.py`, and click "Run Script"
     - **Option B:** Run from terminal: (**Note:** Change paths to Blender and Python files where needed)

       ```bash
       # macOS
       /Applications/Blender.app/Contents/MacOS/Blender --background --python /path/to/Utilities/auto_install_zeroconf.py

       # Windows
       "C:\Program Files\Blender Foundation\Blender 5.0\blender.exe" --background --python "C:\path\to\Utilities\auto_install_zeroconf.py"

       # Linux
       ~/blender-5.0.0-linux-x64/blender --background --python /path/to/Utilities/auto_install_zeroconf.py
       ```

   - Restart Blender after installation

#### **Manual Install (Fallback)**

If auto-installation fails:

1. **Locate Blender's Python:**

   - **macOS:** `/Applications/Blender.app/Contents/Resources/5.0/python/bin/python3.11`
   - **Windows:** `C:\Program Files\Blender Foundation\Blender 5.0\5.0\python\bin\python.exe`
   - **Linux:** `~/blender-5.0.0-linux-x64/5.0/python/bin/python3`

2. **Note:** Replace `5.0` with your installed Blender version (e.g., `4.4`, `4.5`, etc.)

3. **Install via terminal:**

   ```bash
   "<path_to_blender_python>" -m pip install --user zeroconf
   ```

4. **Verify:** Check Blender's System Console (Window > Toggle System Console) for "✓ zeroconf loaded"

5. **Note:** The add-on's warning message "Requires a Vision Pro application..." in Preferences is informational only and will always appear, even when zeroconf is properly installed.

### **2. Vision Pro Application Setup**

1. **Open the Xcode project:**

   - Open `VisionPro Blender Streamer.xcodeproj` in Xcode

2. **Configure Info.plist (Already configured, but verify):**

   - `NSBonjourServices` contains: `_visionpro_blender._tcp.` and `_visionpro_blender._udp.`
   - `NSLocalNetworkUsageDescription` is set for local network permissions

3. **Build and Deploy:**

   - Select your Vision Pro device or Simulator
   - Build and run (⌘R)
   - Grant local network permissions when prompted

4. **Note:** The app advertises as "MyVisionPro" on port **8080**

## **Usage**

### **Quick Start**

1. **Launch Vision Pro App**

   - Open the app on your Vision Pro
   - Tap "Toggle Immersive Space" to enter mixed reality mode
   - App automatically advertises as "MyVisionPro" and listens on port 8080

2. **Open Blender**

   - Launch Blender with the add-on enabled
   - Press `N` in the 3D Viewport to open the sidebar
   - Navigate to the **"Vision Pro"** tab

3. **Connect to Vision Pro**

   - Click **"Start Discovery"**
   - Wait for "MyVisionPro" to appear in the dropdown (usually 2-5 seconds)
   - Select your device from the list
   - Click **"Connect"**
   - Status should show: "Connected to MyVisionPro"

4. **Start Streaming**
   - Click **"Start Streaming"**
   - Your scene will appear in Vision Pro's immersive space
   - Make changes in Blender to see real-time updates

### **Streaming Options**

**Stream FPS:** Controls update frequency (1-60 FPS, default: 30)

- Higher FPS = smoother updates, more CPU usage
- Lower FPS = less resource intensive

**Stream Only When Active:** (Recommended)

- ☑ **Enabled:** Streams only when you're editing (moving objects, modifying meshes, etc.)
- ☐ **Disabled:** Streams continuously at set FPS
- **Inactivity Threshold:** Seconds of idle time before pausing (default: 2.0s)

### **Workflow Tips**

- **Debugging:** Open System Console (Window > Toggle System Console on Windows, or launch from Terminal on macOS/Linux)
- **Performance:** Enable "Stream Only When Active" to reduce CPU/network load
- **Scene Position:** Models appear 1m up, 2m forward from your position in Vision Pro
- **Stopping:** Click "Stop Streaming" to pause, "Disconnect" to close connection

## **Troubleshooting**

### **Dependency Issues**

**"zeroconf not found" warning:**

1. Run `Utilities/auto_install_zeroconf.py` with Blender's Python:
   - Open Blender's Scripting workspace, open the file, and click "Run Script"
   - Or run from terminal: `/Applications/Blender.app/Contents/MacOS/Blender --background --python /path/to/Utilities/auto_install_zeroconf.py`
2. Check System Console for installation errors
3. If auto-install fails, use manual installation method (see Installation)
4. Restart Blender after installation
5. To uninstall, run `Utilities/uninstall_zeroconf.py` the same way:

   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender --background --python /path/to/Utilities/uninstall_zeroconf.py
   ```

### **Connection Issues**

**"Connection failed" / "BrokenPipeError":**

- ✓ Vision Pro app is running and in immersive space
- ✓ Both devices on same Wi-Fi network (not cellular/hotspot)
- ✓ Vision Pro granted "Local Network" permission (Settings > Privacy)
- ✓ Port 8080 is not blocked by firewall
- ✓ Service type matches: `_visionpro_blender._tcp.`

**No devices found in discovery:**

- Wait 10-15 seconds after clicking "Start Discovery"
- Restart Vision Pro app
- Click "Stop Discovery" then "Start Discovery" again
- Check System Console for Bonjour errors
- Verify Info.plist has `NSBonjourServices` with both `_visionpro_blender._tcp.` and `_visionpro_blender._udp.`

### **Streaming Issues**

**"USDZ Export Error: keyword unrecognized":**

- Your Blender version may have different USD export parameters
- Edit `vision_pro_streamer_zeroconf.py`, find `bpy.ops.wm.usd_export()`
- Remove problematic parameters (e.g., `usdz_downscale_size`)
- Consult Blender Python API docs for your version

**Scene not updating in Vision Pro:**

- Check "Realtime Status" message in Blender panel
- Verify "Stream Only When Active" isn't pausing due to inactivity
- Ensure you're making changes that trigger depsgraph updates
- Try disabling "Stream Only When Active" for continuous streaming
- Large or complex scenes may take longer to export and transfer—check System Console for timing

**Performance issues:**

- Lower Stream FPS (try 15-20 FPS)
- Enable "Stream Only When Active"
- Reduce scene complexity: lower poly counts, simplify materials, or optimize textures

### **UI Issues**

**Device list empty/UI sections disappear:**

- Disable and re-enable add-on in Preferences
- Check System Console for Python errors
- Ensure `enum_items_cache` is updating (debug output in console)
- Restart Blender if UI becomes unresponsive

## **Technical Details**

### **Architecture**

**Blender Add-on:**

- Zeroconf service browser for device discovery
- TCP client connecting to Vision Pro on port 8080
- Depsgraph handler for activity detection
- Threaded USDZ export and streaming
- Temporary file management for each export cycle

**Vision Pro App:**

- NetService (Bonjour) advertiser
- NWListener (Network framework) TCP server
- AsyncStream for entity updates to RealityKit
- Temporary USDZ file processing
- Mixed immersion mode rendering

### **Data Flow**

1. Vision Pro advertises `_visionpro_blender._tcp.` and `_visionpro_blender._udp.` on port 8080
2. Blender discovers service via Zeroconf
3. Blender establishes TCP connection
4. On scene change (or timer), Blender exports USDZ to temp file
5. USDZ data sent with 4-byte length header (big-endian)
6. Vision Pro receives, writes to temp file, loads as Entity
7. Entity replaces previous scene in immersive space

### **Customization**

**Change service name:** Edit `VisionProServiceAdvertiser.swift`, line 16:

```swift
netService = NetService(domain: "local.", type: serviceType, name: "YourCustomName", port: servicePort)
```

**Change port:** Update both files:

- `VisionProServiceAdvertiser.swift`: `servicePort = 8080`
- `BlenderSceneReceiver.swift`: `init(port: 8080)`

**Adjust scene position:** Edit `ImmersiveView.swift`, line 32:

```swift
dynamicContentAnchor.transform.translation = SIMD3<Float>(x: 0.0, y: 1.0, z: -2.0)
```

## **Licensing**

This project is licensed under the **BSD 3-Clause License**.

Copyright (c) 2025-2026, Southwest Airlines
All rights reserved.

**Note on Blender Add-on Licensing:**
Blender is licensed under the GNU GPL. Add-ons using Blender's Python API may be considered derivative works under some GPL interpretations. For commercial distribution, consult legal counsel or consider GPLv3 licensing.

## **Known Limitations**

- **Network Only:** Requires both devices on same local network (no internet/cloud streaming)
- **USDZ Format:** Limited to features supported by USD/USDZ (some Blender features may not export)
- **Single Connection:** Vision Pro app accepts one Blender connection at a time
- **No Animation Playback:** Exports static scenes only (animation export disabled for performance)
- **Temporary Files:** Creates temp files for each export (cleaned up automatically)
- **Scene Complexity:** High-poly models or complex materials may take longer to export and stream—start with simpler scenes for best experience

## **Acknowledgements**

- Uses `python-zeroconf` library (LGPL-2.1-or-later)
- Built on Blender Python API and Apple VisionOS/RealityKit frameworks
- Created by Justin Leger (2025)

## **Contributing**

Contributions welcome! Please:

- Open issues for bugs or feature requests
- Submit pull requests with clear descriptions
- Follow existing code style and structure
- Test on both Blender and Vision Pro before submitting
