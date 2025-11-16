//
//  VisionPro_Blender_StreamerApp.swift
//  VisionPro Blender Streamer
//
//  Created by Justin Leger on 6/23/25.
//

import SwiftUI

@main
struct VisionPro_Blender_StreamerApp: App {

    @State private var appModel = AppModel()

    var body: some Scene {
        WindowGroup {
            MainView()
                .environment(appModel)
        }
        .defaultLaunchBehavior(.presented)
        
        WindowGroup(id: appModel.volumeID) {
            VolumeView()
                .environment(appModel)
                .onAppear {
                    appModel.volumeState = .open
                }
                .onDisappear {
                    appModel.volumeState = .closed
                }
        }
        .windowStyle(.volumetric)
        .defaultSize(width: 1, height: 1, depth: 1, in: .meters)
        .restorationBehavior(.disabled)
        .defaultLaunchBehavior(.suppressed)

        ImmersiveSpace(id: appModel.immersiveSpaceID) {
            ImmersiveView()
                .environment(appModel)
                .onAppear {
                    appModel.immersiveSpaceState = .open
                }
                .onDisappear {
                    appModel.immersiveSpaceState = .closed
                }
        }
        .immersionStyle(selection: .constant(.mixed), in: .mixed)
        .restorationBehavior(.disabled)
        .defaultLaunchBehavior(.suppressed)
     }
}
