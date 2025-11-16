//
//  MainView.swift
//  VisionPro Blender Streamer
//
//  Created by Justin Leger on 6/23/25.
//

import SwiftUI
import RealityKit
import RealityKitContent

struct MainView: View {
    
    @Environment(AppModel.self) var appModel
    @Environment(\.openWindow) var openWindow

    var body: some View {
        VStack {
            
            Spacer()
            
            Text("Vision Pro Blender Streamer")
                .font(.title)
            
            Text(appModel.receiver.statusMessage)
            
            Spacer()
            
            LaunchButtons()
            
            Spacer()
        }
        .padding()
        // TODO: Move this methods from the view to the AppModel
        .task {
            for await newEntity in appModel.receiver.sceneEntityUpdates {
                // When a new entity arrives, replace the content of the dynamic anchor.
                // This removes the old scene and adds the new one efficiently.
                appModel.dynamicContentAnchor.children.removeAll()
                appModel.dynamicContentAnchor.addChild(newEntity)
                print("RealityView's dynamic content updated via AsyncStream.")
            }
            print("AsyncStream for entities finished in RealityView.")
        }
        .onAppear{
            appModel.start()
        }
    }
}

#Preview(windowStyle: .automatic) {
    MainView()
        .environment(AppModel())
}
