//
//  ImmersiveView.swift
//  VisionPro Blender Streamer
//
//  Created by Justin Leger on 6/22/25.
//

import SwiftUI
import RealityKit
import RealityKitContent

struct ImmersiveView: View {
    // The main container entity for dynamic content.
    // This will hold the current Blender scene.
    @State private var dynamicContentAnchor = AnchorEntity()
    
    // StateObject for receiver to observe its statusMessage and access its entity stream
    @StateObject private var receiver: BlenderSceneReceiver
    // State for the advertiser (no @Published properties, so @State is fine)
    @State private var advertiser: VisionProServiceAdvertiser
    
    init() {
        // Initialize the receiver and advertiser instances.
        // We can directly use the init of the classes as they no longer need complex closures.
        _receiver = StateObject(wrappedValue: BlenderSceneReceiver(port: 8080))
        _advertiser = State(wrappedValue: VisionProServiceAdvertiser())
    }
    
    var body: some View {
        VStack {
            RealityView { content, attachments in
                // Set the initial position of the anchor:
                // 1.0 meter up (positive Y)
                // -2.0 meters forward (negative Z, since RealityKit's Z-axis is "backwards" relative to user direction)
                dynamicContentAnchor.transform.translation = SIMD3<Float>(x: 0.0, y: 1.0, z: -2.0)
                
                // Add the main anchor for dynamic content to the RealityView's scene
                content.add(dynamicContentAnchor)
                
                // Optional: Add a placeholder or guide initially
                if let placeholder = attachments.entity(for: "placeholder") {
                    // Position the placeholder relative to the anchor, or as an absolute position if desired.
                    // For now, it will be at the origin of the RealityView's space, not attached to dynamicContentAnchor
                    // To attach it to dynamicContentAnchor, you'd add it as a child:
                    // dynamicContentAnchor.addChild(placeholder)
                    // Or keep it separate if it's a fixed UI element.
                    content.add(placeholder)
                }
            }
            update : {_,_ in }
            attachments: {
                Attachment(id: "placeholder") {
                    Text("Awaiting Blender Scene...")
                        .font(.extraLargeTitle)
                        .padding()
                        .glassBackgroundEffect()
                }
            }
            .gesture(SpatialTapGesture().onEnded { value in
                print("Spatial tap detected in RealityView!")
            })
            .task {
                for await newEntity in receiver.sceneEntityUpdates {
                    // When a new entity arrives, replace the content of the dynamic anchor.
                    // This removes the old scene and adds the new one efficiently.
                    dynamicContentAnchor.children.removeAll()
                    dynamicContentAnchor.addChild(newEntity)
                    print("RealityView's dynamic content updated via AsyncStream.")
                }
                print("AsyncStream for entities finished in RealityView.")
            }
            
            // UI to show connection/stream status from the receiver
            Text(receiver.statusMessage)
                .font(.title2)
                .padding()
                .glassBackgroundEffect()
        }
        .onAppear {
            // Start Bonjour advertising and TCP listening when the view appears
            advertiser.startAdvertising()
            receiver.startListening()
        }
        .onDisappear {
            // Stop services when the view disappears
            advertiser.stopAdvertising()
            receiver.stopListening()
            // The Task in RealityView will also be cancelled automatically on disappear
        }
    }
}

#Preview(immersionStyle: .mixed) {
    ImmersiveView()
        .environment(AppModel())
}
