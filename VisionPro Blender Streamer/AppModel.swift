//
//  AppModel.swift
//  VisionPro Blender Streamer
//
//  Created by Justin Leger on 6/23/25.
//

import SwiftUI
import RealityKit

/// Maintains app-wide state
@MainActor
@Observable
class AppModel {
    let immersiveSpaceID = "ImmersiveSpace"
    let volumeID = "VolumeWindow"
    
    enum ImmersiveSpaceState {
        case closed
        case inTransition
        case open
    }
    
    enum VolumeState {
        case closed
        case open
    }
    
    var immersiveSpaceState = ImmersiveSpaceState.closed
    var volumeState: VolumeState = .closed
    
    
    var receiver: BlenderSceneReceiver
    var advertiser: VisionProServiceAdvertiser
    
    let dynamicContentAnchor = Entity()
    
    
    init() {
        // Initialize the receiver and advertiser instances.
        // We can directly use the init of the classes as they no longer need complex closures.
        receiver = BlenderSceneReceiver(port: 8080)
        advertiser = VisionProServiceAdvertiser()
        
        
    }
    
    
    func start(){
        // Start Bonjour advertising and TCP listening when the view appears
        advertiser.startAdvertising()
        receiver.startListening()
    }
    
    func stop(){
        // Stop services when the view disappears
        advertiser.stopAdvertising()
        receiver.stopListening()
    }
}


