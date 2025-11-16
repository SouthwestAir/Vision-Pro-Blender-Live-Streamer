import bpy
import sys
import threading
import socket
import os
import time
import tempfile
import shutil

# --- DEPENDENCY CHECK ---
try:
    from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf, ServiceInfo
    ZEROCONF_AVAILABLE = True
except ImportError:
    print("Warning: 'zeroconf' library not found. Attempting auto-installation...")
    ZEROCONF_AVAILABLE = False
    
    # Attempt auto-installation
    try:
        import subprocess
        import ensurepip
        
        user_scripts = bpy.utils.script_path_user() or bpy.utils.user_resource('SCRIPTS')
        modules_dir = os.path.join(user_scripts, "modules")
        os.makedirs(modules_dir, exist_ok=True)
        
        if modules_dir not in sys.path:
            sys.path.append(modules_dir)
        
        print(f"Target modules dir: {modules_dir}")
        print(f"Python executable: {sys.executable}")
        
        # Ensure pip is available
        try:
            ensurepip.bootstrap()
            print("✓ pip available")
        except Exception as pip_err:
            print(f"Warning: ensurepip failed ({pip_err}), assuming pip exists")
        
        print("Installing zeroconf...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--target", modules_dir, "zeroconf"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"✗ pip install failed:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, result.args)
        
        print("✓ Installation complete")
        
        # Try importing again
        from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf, ServiceInfo
        ZEROCONF_AVAILABLE = True
        print("✓ zeroconf loaded successfully!")
    except (subprocess.CalledProcessError, OSError, ImportError) as e:
        print(f"✗ Auto-installation failed: {e}")
        print(f"Please run auto_install_zeroconf.py from Blender's Scripting workspace.")
        print(f"Or manually install: {sys.executable} -m pip install --target {modules_dir} zeroconf")
        ZEROCONF_AVAILABLE = False 

# --- ADD-ON INFORMATION ---
bl_info = {
    "name": "Vision Pro Streamer (Zeroconf)",
    "author": "Your Name",
    "version": (0, 0, 27),
    "blender": (4, 4, 0),
    "location": "3D Viewport > Sidebar > Vision Pro",
    "description": "Stream Blender scene to Apple Vision Pro in real-time via Zeroconf (mDNS/DNS-SD).",
    "warning": "Requires a Vision Pro application to receive data and 'zeroconf' Python package.",
    "category": "Development",
}

# --- GLOBAL VARIABLES ---
vision_pro_devices = {}
vision_pro_devices_lock = threading.Lock()
current_connection = None
current_connection_lock = threading.Lock()
streaming_thread = None
stop_streaming_event = threading.Event()
zeroconf_instance = None
zeroconf_browser = None
last_model_change_time = 0.0
last_model_change_time_lock = threading.Lock()
is_exporting_usdz = False
export_lock = threading.Lock()
pending_changes_during_export = False
pending_changes_lock = threading.Lock() 

def depsgraph_handler_update_time(scene):
    """
    Blender handler function triggered after dependency graph updates.
    Updates `last_model_change_time` global if not currently exporting USDZ.
    This helps filter out updates caused by the export process itself from user activity.
    """
    global last_model_change_time, is_exporting_usdz, last_model_change_time_lock, pending_changes_during_export, pending_changes_lock
    if not is_exporting_usdz:
        with last_model_change_time_lock:
            last_model_change_time = time.time()
        # print(f"DEBUG: depsgraph_update_post triggered at {last_model_change_time} (not exporting)")
    else:
        # Mark that changes occurred during export
        with pending_changes_lock:
            pending_changes_during_export = True


# --- ZEROCONF LISTENER CLASS ---
if ZEROCONF_AVAILABLE: 
    class VisionProServiceListener:
        """
        Listener class for Zeroconf ServiceBrowser.
        Handles service 'add', 'remove', and 'update' events from the network.
        """
        def add_service(self, zeroconf: Zeroconf, service_type: str, name: str):
            """Called when a new service is discovered."""
            try:
                info = zeroconf.get_service_info(service_type, name)
                if info:
                    # Convert byte addresses to string IPs for storage
                    addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
                    
                    print(f"Service ADDED: {name} Type: {service_type} Host: {info.server} Port: {info.port} Addresses: {addresses}")
                    
                    with vision_pro_devices_lock:
                        vision_pro_devices[info.name] = {
                            'host': info.server,
                            'port': info.port,
                            'addresses': addresses
                        }
                    # Schedule a UI update on Blender's main thread
                    if not bpy.app.timers.is_registered(update_device_list):
                        bpy.app.timers.register(update_device_list, first_interval=0.1)
            except (OSError, RuntimeError) as e:
                print(f"ERROR: Failed to add service {name}: {e}")

        def remove_service(self, zeroconf: Zeroconf, service_type: str, name: str):
            """Called when a service disappears from the network."""
            try:
                print(f"Service REMOVED: {name}")
                with vision_pro_devices_lock:
                    if name in vision_pro_devices:
                        del vision_pro_devices[name]
                # Schedule a UI update on Blender's main thread
                if not bpy.app.timers.is_registered(update_device_list):
                    bpy.app.timers.register(update_device_list, first_interval=0.1)
            except (KeyError, RuntimeError) as e:
                print(f"ERROR: Failed to remove service {name}: {e}")

        def update_service(self, zeroconf: Zeroconf, service_type: str, name: str):
            """Called when an existing service's information changes."""
            # For simplicity, re-adding the service will update its info.
            self.add_service(zeroconf, service_type, name)


    def update_device_list():
        """
        Updates the list of discovered devices in the Blender UI (EnumProperty).
        Manages selection state and forces a UI redraw.
        This function runs on Blender's main thread via bpy.app.timers.
        """
        try:
            print(f"DEBUG: update_device_list called. Current devices: {list(vision_pro_devices.keys())}")

            items_for_enum = []
            with vision_pro_devices_lock:
                for name, data in vision_pro_devices.items():
                    display_name = name.split('.')[0]
                    items_for_enum.append((name, display_name, f"Host: {data['host']}, Port: {data['port']}, IPs: {', '.join(data['addresses'])}"))
        
            # Ensure a "No devices found" option is always present if no devices are discovered
            if not items_for_enum:
                items_for_enum.append( ("NONE", "No devices found", "No Vision Pro devices discovered yet.") )
            
            # Store the current list items for the EnumProperty to read.
            # This acts as a signal for Blender that the enum's underlying data might have changed.
            bpy.context.scene.vision_pro_streamer_props.enum_items_cache = str(items_for_enum) 

            # --- Manage selection state to prevent UI errors ---
            current_selection = bpy.context.scene.vision_pro_streamer_props.selected_device_name
            valid_identifiers = [item[0] for item in items_for_enum]

            if current_selection not in valid_identifiers:
                print(f"DEBUG: Current selection '{current_selection}' invalid. Updating selection.")
                if valid_identifiers and valid_identifiers[0] != "NONE": 
                    bpy.context.scene.vision_pro_streamer_props.selected_device_name = valid_identifiers[0]
                    bpy.context.scene.vision_pro_streamer_props.status_message = "Selected first discovered device."
                    print(f"DEBUG: New selection: {valid_identifiers[0]}")
                elif "NONE" in valid_identifiers: 
                    bpy.context.scene.vision_pro_streamer_props.selected_device_name = "NONE"
                    bpy.context.scene.vision_pro_streamer_props.status_message = "No Vision Pro devices found."
                    print("DEBUG: New selection: NONE")
                else: 
                    bpy.context.scene.vision_pro_streamer_props.selected_device_name = ""
                    bpy.context.scene.vision_pro_streamer_props.status_message = "Device list cleared."
                    print("DEBUG: New selection: '' (cleared)")
            else:
                print(f"DEBUG: Current selection '{current_selection}' is still valid.")

            bpy.context.scene.vision_pro_streamer_props.needs_ui_update = True 

            # Force UI redraw
            for window in bpy.context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()
                        break
            print("DEBUG: UI redraw triggered.")
        except (AttributeError, KeyError, RuntimeError) as e:
            print(f"ERROR: Failed to update device list: {e}")
        return None


    def zeroconf_daemon_thread(zc_instance):
        """
        Runs the Zeroconf instance in a separate daemon thread to perform discovery.
        This prevents the discovery process from blocking Blender's UI.
        """
        try:
            while True:
                time.sleep(1) # Keep thread alive while Zeroconf works internally
        except (KeyboardInterrupt, RuntimeError) as e:
            print(f"ERROR: Zeroconf daemon thread error: {e}")
        finally:
            print("INFO: Zeroconf daemon thread exiting.")

# --- OPERATORS ---

class VSP_OT_DiscoverVisionPro(bpy.types.Operator):
    """Operator to start Bonjour/Zeroconf discovery for Vision Pro devices."""
    bl_idname = "vision_pro_streamer.discover_vision_pro"
    bl_label = "Discover Vision Pros"
    bl_description = "Starts Zeroconf (mDNS/DNS-SD) discovery for Vision Pro devices."

    @classmethod
    def poll(cls, context):
        """Ensures the operator can only run if Zeroconf is available and no discovery is active."""
        global zeroconf_instance
        return ZEROCONF_AVAILABLE and zeroconf_instance is None

    def execute(self, context):
        """Executes the discovery process."""
        global zeroconf_instance, zeroconf_browser, vision_pro_devices
        
        if not ZEROCONF_AVAILABLE: 
            self.report({'ERROR'}, "python-zeroconf library not found. Cannot perform discovery.")
            return {'CANCELLED'}

        self.report({'INFO'}, "Starting Zeroconf discovery...")
        context.scene.vision_pro_streamer_props.status_message = "Discovering..."
        with vision_pro_devices_lock:
            vision_pro_devices.clear() # Clear any previously discovered devices
        
        # Immediately update UI to reflect clearing of devices and "No devices found"
        bpy.app.timers.register(update_device_list, first_interval=0.01)

        # Define the service type and domain that the Vision Pro app is expected to advertise
        # These match the Swift NetService parameters: domain and type
        service_domain = "local."
        service_type = "_visionpro_blender._tcp."
        # Concatenate to form the full service string for Zeroconf
        full_service_type = service_type + service_domain

        try:
            zeroconf_instance = Zeroconf()
            listener = VisionProServiceListener()
            zeroconf_browser = ServiceBrowser(zeroconf_instance, full_service_type, listener)
            
            # Start the Zeroconf daemon in a separate thread
            t = threading.Thread(target=zeroconf_daemon_thread, args=(zeroconf_instance,))
            t.daemon = True # Allow Blender to exit even if this thread is running
            t.start()
            
        except (OSError, RuntimeError) as e:
            self.report({'ERROR'}, f"Zeroconf Error: {e}. Check network configuration.")
            context.scene.vision_pro_streamer_props.status_message = f"Discovery Error: {e}"
            if zeroconf_instance:
                try:
                    zeroconf_instance.close()
                except (OSError, RuntimeError):
                    pass
                zeroconf_instance = None
            return {'CANCELLED'}

        return {'FINISHED'}

class VSP_OT_StopDiscovery(bpy.types.Operator):
    """Operator to stop the ongoing Bonjour/Zeroconf discovery."""
    bl_idname = "vision_pro_streamer.stop_discovery"
    bl_label = "Stop Discovery"
    bl_description = "Stops the ongoing Zeroconf discovery."

    @classmethod
    def poll(cls, context):
        """Ensures the operator can only run if discovery is active."""
        return ZEROCONF_AVAILABLE and zeroconf_instance is not None 

    def execute(self, context):
        """Executes the stop discovery process."""
        global zeroconf_instance, zeroconf_browser
        if zeroconf_browser:
            zeroconf_browser = None 
        if zeroconf_instance:
            zeroconf_instance.close() # Close the Zeroconf instance to stop its internal threads
            zeroconf_instance = None
            self.report({'INFO'}, "Zeroconf discovery stopped.")
            context.scene.vision_pro_streamer_props.status_message = "Discovery stopped."
            with vision_pro_devices_lock:
                vision_pro_devices.clear()
            bpy.app.timers.register(update_device_list, first_interval=0.1) # Update UI to reflect empty list
        return {'FINISHED'}


class VSP_OT_ConnectToVisionPro(bpy.types.Operator):
    """Operator to establish a TCP/IP connection to the selected Vision Pro."""
    bl_idname = "vision_pro_streamer.connect_vision_pro"
    bl_label = "Connect"
    bl_description = "Connects to the selected Vision Pro device."

    @classmethod
    def poll(cls, context):
        """Ensures operator is enabled only if a device is selected and not already connected."""
        props = context.scene.vision_pro_streamer_props
        # Check if a device is selected, exists in our discovered list, and no current connection.
        return props.selected_device_name and props.selected_device_name in vision_pro_devices and current_connection is None

    def execute(self, context):
        """Executes the connection attempt."""
        global current_connection
        props = context.scene.vision_pro_streamer_props
        device_full_name = props.selected_device_name 
        
        with vision_pro_devices_lock:
            if device_full_name not in vision_pro_devices:
                self.report({'ERROR'}, "Selected device not found or no longer available.")
                return {'CANCELLED'}
            device_info = vision_pro_devices[device_full_name].copy()
        
        # Prefer an explicit IP address if available, otherwise use the mDNS hostname.
        target_host = device_info['addresses'][0] if device_info['addresses'] else device_info['host']
        target_port = device_info['port']

        self.report({'INFO'}, f"Attempting to connect to {target_host}:{target_port}...")
        context.scene.vision_pro_streamer_props.status_message = f"Connecting to {target_host}:{target_port}..."

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            s.settimeout(5) # Set a timeout for the connection attempt
            s.connect((target_host, target_port))
            s.settimeout(None)
            with current_connection_lock:
                current_connection = s
            self.report({'INFO'}, f"Successfully connected to {device_full_name.split('.')[0]}!")
            context.scene.vision_pro_streamer_props.status_message = f"Connected to {device_full_name.split('.')[0]}"
            print(f"DEBUG: Socket connection established: {current_connection}")
        except socket.error as e:
            self.report({'ERROR'}, f"Connection failed: {e}")
            context.scene.vision_pro_streamer_props.status_message = f"Connection failed: {e}"
            with current_connection_lock:
                current_connection = None
            print(f"DEBUG: Socket connection failed: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}

class VSP_OT_DisconnectVisionPro(bpy.types.Operator):
    """Operator to disconnect from the current Vision Pro connection."""
    bl_idname = "vision_pro_streamer.disconnect_vision_pro"
    bl_label = "Disconnect"
    bl_description = "Disconnects from the Vision Pro device."

    @classmethod
    def poll(cls, context):
        """Ensures operator is enabled only if a connection exists."""
        return current_connection is not None

    def execute(self, context):
        """Executes the disconnection process."""
        global current_connection, streaming_thread, stop_streaming_event
        
        print("DEBUG: DisconnectVisionPro called.")
        # If streaming is active, signal it to stop first.
        if streaming_thread and streaming_thread.is_alive():
            print("DEBUG: Signaling streaming thread to stop.")
            stop_streaming_event.set()
            streaming_thread.join(timeout=2) # Wait for the thread to terminate gracefully
            if streaming_thread.is_alive():
                print("Warning: Streaming thread did not terminate gracefully.")
            streaming_thread = None
            stop_streaming_event.clear() # Clear the event for future use
            bpy.context.scene.vision_pro_streamer_props.is_streaming = False

        if current_connection:
            try:
                print("DEBUG: Shutting down and closing socket.")
                current_connection.shutdown(socket.SHUT_RDWR) # Attempt graceful shutdown
            except (socket.error, OSError):
                pass  # Socket may already be closed
            finally:
                try:
                    current_connection.close()
                except (socket.error, OSError):
                    pass
                with current_connection_lock:
                    current_connection = None
                self.report({'INFO'}, "Disconnected from Vision Pro.")
                bpy.context.scene.vision_pro_streamer_props.status_message = "Disconnected."
            
        return {'FINISHED'}

# --- STREAMING LOGIC ---
def stream_scene_data(sock, stop_event):
    """
    Function executed in a separate thread to continuously export and stream Blender scene data.
    Implements activity-based streaming control.
    """
    global pending_changes_during_export
    print("DEBUG: stream_scene_data thread started.")
    # Schedule initial status update on main thread
    bpy.app.timers.register(lambda: (bpy.context.scene.vision_pro_streamer_props.status_message_realtime_update("Streaming..."), None)[1], first_interval=0.1)

    temp_dir = None 
    try:
        while not stop_event.is_set():
            print("DEBUG: Stream loop iteration started.")
            
            # --- Stream Control Logic (Activity Detection) ---
            scene_props = bpy.context.scene.vision_pro_streamer_props
            if scene_props.stream_only_when_active:
                current_time = time.time()
                with last_model_change_time_lock:
                    idle_duration = current_time - last_model_change_time
                
                is_active = (idle_duration < scene_props.inactivity_threshold)

                if not is_active:
                    status_msg = f"Streaming (Idle: No activity for {idle_duration:.1f}s)"
                    
                    print(f"DEBUG: Skipping stream update: {status_msg}")
                    # Update status message on UI
                    bpy.app.timers.register(lambda msg=status_msg: (bpy.context.scene.vision_pro_streamer_props.status_message_realtime_update(msg), None)[1], first_interval=0.1) 
                    time.sleep(0.5) # Sleep longer when idle to reduce CPU usage
                    continue # Skip the rest of the loop iteration (no export/send)
                else:
                    print("DEBUG: User is active. Proceeding with stream update.")
            # --- End Stream Control Logic ---

            # Check if export is already in progress
            if not export_lock.acquire(blocking=False):
                print("DEBUG: Export already in progress, skipping this cycle.")
                continue

            try:
                # Create a unique temporary directory for each export cycle to prevent conflicts
                temp_dir = tempfile.mkdtemp(prefix="blender_vppro_")
                print(f"DEBUG: Created temporary directory: {temp_dir}")
                
                temp_usdz_path = os.path.join(temp_dir, "scene_export.usdz")
                
                usdz_data = None 
                event = threading.Event() # Event to signal completion of main-thread export

                # Function to be executed on Blender's main thread for USDZ export
                def export_usdz_in_main_thread_cb():
                    nonlocal usdz_data
                    global is_exporting_usdz # Declare global to modify the flag
                    try:
                        is_exporting_usdz = True # Set flag to True: subsequent depsgraph updates will be ignored
                        print("DEBUG: Initiating USDZ export in main thread.") 
                        if bpy.context.view_layer is None:
                            print("WARNING: No active view layer context for USDZ export. Export might fail.") 
                        
                        # Call Blender's USD exporter.
                        # Note: Arguments used here are generally supported across recent Blender versions.
                        # If specific arguments cause "unrecognized keyword" errors in your Blender build,
                        # remove them. Blender's exporter intelligently bundles textures into USDZ.
                        bpy.ops.wm.usd_export(
                            filepath=temp_usdz_path, 
                            check_existing=False,
                            # Standard export options for a robust USDZ output
                            selected_objects_only=False,  # Export all visible objects
                            export_materials=True,        # Export materials (as USD Preview Surface)
                            export_normals=True,          # Export vertex normals
                            export_uvmaps=True,           # Export UV maps
                            export_mesh_colors=False,     # Export vertex colors
                            export_animation=False,       # Export animations
                            export_cameras=False,         # Export scene cameras
                            export_lights=False           # Export scene lights
                        )
                        with open(temp_usdz_path, 'rb') as f: 
                            usdz_data = f.read() 
                        
                        print(f"DEBUG: USDZ exported to temp file and read: {len(usdz_data)} bytes.") 

                    except (RuntimeError, OSError, IOError) as e:
                        print(f"ERROR: USDZ Export Error: {e}") 
                        error_msg = str(e)
                        bpy.app.timers.register(lambda msg=error_msg: (bpy.context.scene.vision_pro_streamer_props.status_message_realtime_update(f"Export Error: {msg}"), None)[1])
                        usdz_data = None
                    finally:
                        is_exporting_usdz = False # Reset flag after export attempt
                        event.set() # Signal the waiting thread that export is complete
                    return None # Timer callback must return None or a float
                
                # Schedule the export function to run on Blender's main thread and wait for it.
                bpy.app.timers.register(export_usdz_in_main_thread_cb, first_interval=0.01)
                event.wait(timeout=5) # Wait up to 5 seconds for export to complete

                # If export failed or timed out, skip sending this cycle
                if not event.is_set() or usdz_data is None: 
                    print("DEBUG: USDZ export timed out or failed. Skipping send.") 
                    bpy.app.timers.register(lambda: (bpy.context.scene.vision_pro_streamer_props.status_message_realtime_update("USDZ export failed/timed out."), None)[1])
                    time.sleep(1 / bpy.context.scene.render.fps) # Sleep to avoid busy-waiting on rapid failure
                    continue

                # Prepare data for sending: 4-byte length prefix + USDZ data
                data_length = len(usdz_data) 
                header = data_length.to_bytes(4, 'big')

                print(f"DEBUG: Attempting to send {data_length} bytes to Vision Pro.")
                try:
                    sock.sendall(header + usdz_data) # Send the USDZ data
                    print("DEBUG: Data sent successfully.")
                    
                    # Update status on UI after successful send
                    fps = bpy.context.scene.render.fps
                    bpy.app.timers.register(lambda dl=data_length, f=fps: (bpy.context.scene.vision_pro_streamer_props.status_message_realtime_update(f"Sent {dl/1024:.2f} KB. FPS: {f}"), None)[1])

                    # Pause briefly to control streaming rate
                    time.sleep(1 / fps)
                except (socket.error, OSError) as e:
                    print(f"ERROR: Failed to send data: {e}")
                    raise
            finally:
                export_lock.release()
                
                # Check if changes occurred during export
                with pending_changes_lock:
                    if pending_changes_during_export:
                        pending_changes_during_export = False
                        print("DEBUG: Changes detected during export, forcing immediate re-export.")
                        continue  # Skip sleep, immediately start next iteration

    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError) as e:
        print(f"ERROR: Socket disconnected during streaming: {e}")
        bpy.app.timers.register(lambda: (bpy.ops.vision_pro_streamer.disconnect_vision_pro(), None)[1], first_interval=0.01)
        stop_event.set()
    except socket.error as e:
        print(f"ERROR: Socket error during streaming: {e}")
        bpy.app.timers.register(lambda: (bpy.ops.vision_pro_streamer.disconnect_vision_pro(), None)[1], first_interval=0.01)
        stop_event.set()
    except (RuntimeError, IOError) as e:
        print(f"ERROR: Unexpected streaming error: {e}")
        bpy.app.timers.register(lambda: (bpy.ops.vision_pro_streamer.disconnect_vision_pro(), None)[1], first_interval=0.01)
        stop_event.set()
    finally: # Ensure temporary directory is cleaned up
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir) # Remove the directory and its contents
                print(f"DEBUG: Cleaned up temporary directory: {temp_dir}")
            except OSError as cleanup_e:
                print(f"WARNING: Failed to remove temporary directory {temp_dir}: {cleanup_e}")


    print("DEBUG: Streaming thread stopping.")
    # Final status update on UI after thread stops
    bpy.app.timers.register(lambda: (bpy.context.scene.vision_pro_streamer_props.status_message_realtime_update("Streaming stopped."), None)[1])


class VSP_OT_StartStreaming(bpy.types.Operator):
    """Operator to start real-time scene streaming to Vision Pro."""
    bl_idname = "vision_pro_streamer.start_streaming"
    bl_label = "Start Streaming"
    bl_description = "Starts streaming the current Blender scene to the connected Vision Pro."

    @classmethod
    def poll(cls, context):
        """Checks if operator should be enabled (connected and not already streaming)."""
        poll_result = current_connection is not None and (streaming_thread is None or not streaming_thread.is_alive())
        return poll_result

    def execute(self, context):
        """Executes the start streaming process."""
        global streaming_thread, stop_streaming_event, last_model_change_time 
        
        self.report({'INFO'}, "Starting scene streaming...")
        context.scene.vision_pro_streamer_props.status_message = "Streaming..."
        context.scene.vision_pro_streamer_props.is_streaming = True
        stop_streaming_event.clear() # Ensure the stop event is clear for a new stream
        
        if current_connection is None:
            self.report({'ERROR'}, "Not connected to a Vision Pro.")
            return {'CANCELLED'}

        if streaming_thread and streaming_thread.is_alive():
            self.report({'WARNING'}, "Streaming already active.")
            return {'CANCELLED'}

        if context.scene.vision_pro_streamer_props.stream_only_when_active:
            with last_model_change_time_lock:
                last_model_change_time = time.time()
            print("DEBUG: Resetting last_model_change_time on Start Streaming for active mode.")

        # Create and start the streaming thread
        streaming_thread = threading.Thread(target=stream_scene_data, args=(current_connection, stop_streaming_event))
        streaming_thread.daemon = True # Thread will close automatically when Blender closes
        streaming_thread.start()
        print(f"DEBUG: Streaming thread launched. Is active: {streaming_thread.is_alive()}") 

        # Force UI redraw to update button states
        try:
            for window in bpy.context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()
                        break
        except (AttributeError, RuntimeError) as e:
            print(f"WARNING: Failed to redraw UI: {e}")

        return {'FINISHED'}

class VSP_OT_StopStreaming(bpy.types.Operator):
    """Operator to stop real-time scene streaming."""
    bl_idname = "vision_pro_streamer.stop_streaming"
    bl_label = "Stop Streaming"
    bl_description = "Stops streaming the Blender scene."

    @classmethod
    def poll(cls, context):
        """Checks if operator should be enabled (only if streaming is active)."""
        poll_result = streaming_thread is not None and streaming_thread.is_alive()
        return poll_result

    def execute(self, context):
        """Executes the stop streaming process."""
        global streaming_thread, stop_streaming_event
        
        self.report({'INFO'}, "Stopping scene streaming...")
        context.scene.vision_pro_streamer_props.status_message = "Stopping streaming..."
        stop_streaming_event.set() # Signal the streaming thread to stop
        
        context.scene.vision_pro_streamer_props.is_streaming = False

        # Force UI redraw to update button states
        try:
            for window in bpy.context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()
                        break
        except (AttributeError, RuntimeError) as e:
            print(f"WARNING: Failed to redraw UI: {e}")

        return {'FINISHED'}

# --- UI PANEL ---
class VSP_PT_VisionProStreamerPanel(bpy.types.Panel):
    """Blender UI Panel for the Vision Pro Streamer add-on."""
    bl_label = "Vision Pro Streamer"
    bl_idname = "VSP_PT_VisionProStreamerPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vision Pro" # Category in the N-panel (sidebar)

    def draw(self, context):
        """Draws the UI elements in the panel."""
        layout = self.layout
        scene_props = context.scene.vision_pro_streamer_props 

        # Discovery Section
        box = layout.box()
        box.label(text="Discovery", icon='WORLD')
        if not ZEROCONF_AVAILABLE:
            box.label(text="'zeroconf' not found. See console for installation.", icon='INFO')
        else:
            row = box.row()
            row.operator("vision_pro_streamer.discover_vision_pro", icon='FILE_REFRESH', text="Start Discovery")
            row.operator("vision_pro_streamer.stop_discovery", icon='CANCEL', text="Stop Discovery")

            row = box.row()
            row.prop(scene_props, "selected_device_name", text="Discovered Devices")
            
            # The needs_ui_update flag is primarily for internal logic to signal updates.
            # No direct UI drawing logic here.

        # Connection Section
        box = layout.box()
        box.label(text="Connection", icon='LINKED')

        row = box.row(align=True)
        row.operator("vision_pro_streamer.connect_vision_pro", icon='LINKED') 
        row.operator("vision_pro_streamer.disconnect_vision_pro", icon='UNLINKED') 

        # Streaming Section
        box = layout.box()
        box.label(text="Streaming", icon='OUTLINER_OB_LIGHT')
        
        row = box.row(align=True)
        row.enabled = current_connection is not None # Only enable streaming buttons if connected
        row.operator("vision_pro_streamer.start_streaming", icon='PLAY')
        row.operator("vision_pro_streamer.stop_streaming", icon='PAUSE') 
        
        row = box.row()
        row.prop(scene_props, "render_fps", text="Stream FPS")

        # Checkbox for activity-based streaming
        row = box.row()
        row.prop(scene_props, "stream_only_when_active") 
        # Inactivity threshold is only relevant if activity-based streaming is enabled
        row = box.row()
        row.enabled = scene_props.stream_only_when_active 
        row.prop(scene_props, "inactivity_threshold")


        # Status Messages
        layout.separator()
        layout.label(text="Status:")
        layout.label(text=scene_props.status_message, icon='INFO')
        layout.label(text=scene_props.realtime_status_message, icon='RENDER_STILL')

# --- PROPERTIES ---
class VisionProStreamerProperties(bpy.types.PropertyGroup):
    """Collection of custom properties for the Vision Pro Streamer add-on."""
    status_message: bpy.props.StringProperty(
        name="Status",
        default="Idle",
        description="Current status of the add-on."
    )
    realtime_status_message: bpy.props.StringProperty(
        name="Realtime Status",
        default="",
        description="Real-time streaming status (e.g., data sent, errors)."
    )
    
    # Internal cache for discovered devices enum items.
    # Used to ensure the dynamic EnumProperty updates reliably in the UI.
    enum_items_cache: bpy.props.StringProperty(
        name="Enum Items Cache (Internal)",
        default="", 
        description="Internal property to help force EnumProperty refresh."
    )

    def get_discovered_devices_enum(self, context):
        """
        Dynamically generates the items for the 'selected_device_name' EnumProperty.
        Reads directly from the global 'vision_pro_devices' dictionary.
        """
        items = []
        for name, data in vision_pro_devices.items():
            display_name = name.split('.')[0] # Display short name in UI
            items.append((name, display_name, f"Host: {data['host']}, Port: {data['port']}, IPs: {', '.join(data['addresses'])}"))
        
        # Ensure a default "No devices found" option if the list is empty
        if not items:
            items.append( ("NONE", "No devices found", "No Vision Pro devices discovered yet.") )
        
        return items

    selected_device_name: bpy.props.EnumProperty(
        name="Select Device",
        items=get_discovered_devices_enum, # Callable function to provide dynamic items
        description="Select a discovered Apple Vision Pro device."
    )
    
    is_streaming: bpy.props.BoolProperty(
        name="Is Streaming",
        default=False,
        description="Indicates if real-time streaming is currently active."
    )

    render_fps: bpy.props.IntProperty(
        name="Stream FPS",
        description="Frames per second to stream the scene to Vision Pro.",
        default=30,
        min=1,
        max=60
    )

    # Internal flag used by update_device_list to signal UI redraws.
    needs_ui_update: bpy.props.BoolProperty(
        name="Needs UI Update",
        default=False,
        description="Internal flag to trigger UI redraws for dynamic lists."
    )

    stream_only_when_active: bpy.props.BoolProperty(
        name="Stream Only When Active",
        description="Only stream when Blender detects recent changes (user interaction) in any mode.",
        default=False
    )

    inactivity_threshold: bpy.props.FloatProperty(
        name="Inactivity Threshold (s)",
        description="Time in seconds after which streaming pauses if no changes are detected.",
        default=2.0,
        min=0.1,
        max=60.0,
        subtype='FACTOR', 
        unit='TIME' 
    )

    def status_message_realtime_update(self, message):
        """Updates the real-time status message and forces a UI redraw for it."""
        self.realtime_status_message = message
        if bpy.context.area: # Only tag redraw if there's an active area
            bpy.context.area.tag_redraw()


# --- REGISTRATION / UNREGISTRATION ---
classes = (
    VisionProStreamerProperties,
    VSP_OT_DiscoverVisionPro,
    VSP_OT_StopDiscovery,
    VSP_OT_ConnectToVisionPro,
    VSP_OT_DisconnectVisionPro,
    VSP_OT_StartStreaming,
    VSP_OT_StopStreaming,
    VSP_PT_VisionProStreamerPanel,
)

def register():
    """Registers all Blender classes and handlers when the add-on is enabled."""
    for cls in classes:
        bpy.utils.register_class(cls)
    # Register custom scene properties
    bpy.types.Scene.vision_pro_streamer_props = bpy.props.PointerProperty(type=VisionProStreamerProperties)
    
    # Register the depsgraph update handler
    # This handler updates `last_model_change_time` global, crucial for activity detection.
    if depsgraph_handler_update_time not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(depsgraph_handler_update_time)
        print("DEBUG: depsgraph_update_post handler registered.")


def unregister():
    """Unregisters all Blender classes and handlers when the add-on is disabled."""
    # Unregister the depsgraph update handler
    if depsgraph_handler_update_time in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_handler_update_time)
        print("DEBUG: depsgraph_update_post handler unregistered.")

    # Unregister custom scene properties
    del bpy.types.Scene.vision_pro_streamer_props
    # Unregister all custom classes in reverse order
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # Clean up global state and stop any running threads/connections
    global streaming_thread, stop_streaming_event, zeroconf_instance, current_connection, zeroconf_browser
    
    if streaming_thread and streaming_thread.is_alive():
        print("DEBUG: Unregistering: Signaling streaming thread to stop.")
        stop_streaming_event.set()
        streaming_thread.join(timeout=1) # Give thread a moment to shut down
    
    with current_connection_lock:
        if current_connection:
            try:
                print("DEBUG: Unregistering: Shutting down and closing socket.")
                current_connection.shutdown(socket.SHUT_RDWR)
            except (socket.error, OSError):
                pass
            finally:
                try:
                    current_connection.close()
                except (socket.error, OSError) as e:
                    print(f"Error closing connection during unregister: {e}")
    
    if zeroconf_instance:
        print("DEBUG: Unregistering: Closing Zeroconf instance.")
        zeroconf_instance.close()
        time.sleep(0.1) # Give zeroconf a moment to clean up
    
    stop_streaming_event.clear()
    with current_connection_lock:
        current_connection = None
    streaming_thread = None
    zeroconf_instance = None
    zeroconf_browser = None
    with vision_pro_devices_lock:
        vision_pro_devices.clear()

if __name__ == "__main__":
    register()
