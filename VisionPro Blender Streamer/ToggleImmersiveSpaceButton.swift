//
//  ToggleImmersiveSpaceButton.swift
//  VisionPro Blender Streamer
//
//  Created by Justin Leger on 6/23/25.
//

import SwiftUI

struct LaunchButtons: View {

    @Environment(AppModel.self) private var appModel

    @Environment(\.dismissImmersiveSpace) private var dismissImmersiveSpace
    @Environment(\.openImmersiveSpace) private var openImmersiveSpace
    @Environment(\.openWindow) private var openWindow
    @Environment(\.dismissWindow) private var dismissWindow

    var body: some View {
        
        HStack{
            Button {
                Task { @MainActor in
                    if appModel.immersiveSpaceState == .open {
                        appModel.immersiveSpaceState = .inTransition
                        await dismissImmersiveSpace()
                    }
                    
                    switch appModel.volumeState {
                    case .closed:
                        openWindow(id: appModel.volumeID)
                    case .open:
                        dismissWindow(id: appModel.volumeID)
                    }
                }
            } label: {
                Text(appModel.volumeState == .open ? "Close Volume" : "Open Volume")
            }
            
            
            Button {
                Task { @MainActor in
                    
                    if appModel.volumeState == .open {
                        dismissWindow(id: appModel.volumeID)
                    }
                    
                    switch appModel.immersiveSpaceState {
                        case .open:
                            appModel.immersiveSpaceState = .inTransition
                            await dismissImmersiveSpace()
                            // Don't set immersiveSpaceState to .closed because there
                            // are multiple paths to ImmersiveView.onDisappear().
                            // Only set .closed in ImmersiveView.onDisappear().

                        case .closed:
                            appModel.immersiveSpaceState = .inTransition
                            switch await openImmersiveSpace(id: appModel.immersiveSpaceID) {
                                case .opened:
                                    // Don't set immersiveSpaceState to .open because there
                                    // may be multiple paths to ImmersiveView.onAppear().
                                    // Only set .open in ImmersiveView.onAppear().
                                    break

                                case .userCancelled, .error:
                                    // On error, we need to mark the immersive space
                                    // as closed because it failed to open.
                                    fallthrough
                                @unknown default:
                                    // On unknown response, assume space did not open.
                                    appModel.immersiveSpaceState = .closed
                            }

                        case .inTransition:
                            // This case should not ever happen because button is disabled for this case.
                            break
                    }
                }
            } label: {
                Text(appModel.immersiveSpaceState == .open ? "Hide Immersive Space" : "Show Immersive Space")
            }
            .disabled(appModel.immersiveSpaceState == .inTransition)
        }
        .animation(.none, value: 0)
        .fontWeight(.semibold)
    }
}
