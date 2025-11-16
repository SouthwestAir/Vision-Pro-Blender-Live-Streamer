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
    
    @Environment(AppModel.self) var appModel
    
    
    var body: some View {
        VStack {
            RealityView { content, attachments in
                // Set the initial position of the anchor:
                // 1.0 meter up (positive Y)
                // -2.0 meters forward (negative Z, since RealityKit's Z-axis is "backwards" relative to user direction)
                appModel.dynamicContentAnchor.transform.translation = SIMD3<Float>(x: 0.0, y: 1.0, z: -2.0)
                
                // Add the main anchor for dynamic content to the RealityView's scene
                content.add(appModel.dynamicContentAnchor)
                
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
            
            
            // UI to show connection/stream status from the receiver
            Text(appModel.receiver.statusMessage)
                .font(.title2)
                .padding()
                .glassBackgroundEffect()
        }
        
    }
}

#Preview(immersionStyle: .mixed) {
    ImmersiveView()
        .environment(AppModel())
}
