//
//  AppModel.swift
//  VisionPro Blender Streamer
//
//  Created by Justin Leger on 6/23/25.
//

import SwiftUI

/// Maintains app-wide state
@MainActor
@Observable
class AppModel {
    let immersiveSpaceID = "ImmersiveSpace"
    enum ImmersiveSpaceState {
        case closed
        case inTransition
        case open
    }

    var immersiveSpaceState = ImmersiveSpaceState.closed

    // Shared networking services
    let receiver = BlenderSceneReceiver(port: 8080)
    let advertiser = VisionProServiceAdvertiser()

    // Connection status for UI display
    var isConnected: Bool {
        receiver.statusMessage.contains("Connected") || receiver.statusMessage.contains("Loaded")
    }
}
