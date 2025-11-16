//
//  VolumeView.swift
//  VisionPro Blender Streamer
//
//  Created by Juan Alejandro Moya Grajales on 16/11/2025.
//

import SwiftUI
import RealityKit

struct VolumeView: View {
    
    @Environment(AppModel.self) var appModel
    let volumeRootEntity = Entity()
    let aligmentEntity = Entity()
    
    var body: some View {
        
        GeometryReader3D { proxy in
                    RealityView { content in

                        content.add(volumeRootEntity)
                        
                        // TODO: Calculate offset with window height + Add toolbar to select alignemnt (bottom, center,...)
                        aligmentEntity.position = SIMD3<Float>(0, -0.5, 0)
                        
                        // TODO: Find a better way than changing the transform of the appModel.dynamicContentAnchor (see ImmersiveView) => Ideally dynamicContentAnchor should be left untouched
                        appModel.dynamicContentAnchor.transform.translation = SIMD3<Float>(x: 0, y: 0, z: 0)
                        
                        aligmentEntity.addChild(appModel.dynamicContentAnchor)

                        volumeRootEntity.addChild(aligmentEntity)

                    } update: { content in
                        
                        // TODO: The following method scales down the model with the window. Additionally it'd be very useful an option to scaleToFit the model to volume bounds
                        volumeRootEntity.scaleWithVolume(content, proxy)
                        print("Update closure called. current scale: \(volumeRootEntity.scale.x)")

                    }
                    .debugBorder3D(.white)

                }
    }
}

#Preview {
    VolumeView()
}
