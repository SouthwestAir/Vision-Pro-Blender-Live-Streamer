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
    // Access the shared AppModel from the environment
    @Environment(AppModel.self) private var appModel
    
    // The main container entity for dynamic content.
    // This will hold the current Blender scene.
    @State private var dynamicContentAnchor = AnchorEntity()
    
    var body: some View {
        VStack {
            RealityView { content, attachments in
                // Set the position for where the dynamic content group should appear in the world
                dynamicContentAnchor.transform.translation = SIMD3<Float>(x: 0.0, y: 1.0, z: -2.0)
                
                // Manually add the interaction components to the anchor
                dynamicContentAnchor.components.set(InputTargetComponent())
                dynamicContentAnchor.components.set(generateManipulationCompunent())
                
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
                
                // IMPORTANT: The communication between the async stream and the RealityView
                // happens via a task that modifies the anchor's children, not here in the make closure.
                
            }
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
                for await newEntity in appModel.receiver.sceneEntityUpdates {
                    // When a new entity arrives, replace the content of the dynamic anchor.
                    // This removes the old scene and adds the new one efficiently.
                    dynamicContentAnchor.children.removeAll()
                    
                    // Add the new entity received from Blender
                    dynamicContentAnchor.addChild(newEntity)
                    print("RealityView's dynamic content updated via AsyncStream.")
                    
                    // Ensure the anchor itself has collision bounds covering its new children
                    dynamicContentAnchor.updateCollisionShapesFromChildren()
                    
                    print("RealityView's dynamic content updated and configured for manipulation.")
                }
                print("AsyncStream for entities finished in RealityView.")
            }
            
            // UI to show connection/stream status from the receiver
            Text(appModel.receiver.statusMessage)
                .font(.title2)
                .padding()
                .glassBackgroundEffect()
        }
        .onAppear {
            // Start Bonjour advertising and TCP listening when the view appears
            appModel.advertiser.startAdvertising()
            appModel.receiver.startListening()
        }
        .onDisappear {
            // Stop services when the view disappears
            appModel.advertiser.stopAdvertising()
            appModel.receiver.stopListening()
            // The Task in RealityView will also be cancelled automatically on disappear
        }
    }
    
    private func generateManipulationCompunent() -> ManipulationComponent {
        var manipulationComponent = ManipulationComponent()
        
        manipulationComponent.releaseBehavior = .stay
        manipulationComponent.dynamics.translationBehavior = .unconstrained
        manipulationComponent.dynamics.primaryRotationBehavior = .unconstrained
        manipulationComponent.dynamics.secondaryRotationBehavior = .unconstrained
        manipulationComponent.dynamics.scalingBehavior = .unconstrained
        manipulationComponent.dynamics.inertia = .zero
        
        return manipulationComponent
    }
}

#Preview(immersionStyle: .mixed) {
    ImmersiveView()
        .environment(AppModel())
}
