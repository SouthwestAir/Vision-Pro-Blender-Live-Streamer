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
            ContentView()
                .environment(appModel)
        }

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
     }
}
