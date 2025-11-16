//
//  BlenderSceneReceiver.swift
//  VisionPro Blender Streamer
//
//  Created by Justin Leger on 6/23/25.
//

import Foundation
import Network
import RealityKit
import SwiftUI

class BlenderSceneReceiver: NSObject, ObservableObject {
    private var listener: NWListener?
    private var connection: NWConnection?
    private let port: NWEndpoint.Port
    
    // The AsyncStream to send Entity updates
    private var entityUpdateContinuation: AsyncStream<Entity>.Continuation?
    public var sceneEntityUpdates: AsyncStream<Entity>! // Public stream for ContentView
    
    // Publish updates to SwiftUI views
    @Published var statusMessage: String = "Not listening"
    
    init(port: UInt16) {
        self.port = NWEndpoint.Port(rawValue: port)!
        super.init()
        
        // Initialize the AsyncStream. The continuation will be used to yield entities.
        self.sceneEntityUpdates = AsyncStream { continuation in
            self.entityUpdateContinuation = continuation
            
            // Handle stream termination (e.g., when the consumer stops observing)
            continuation.onTermination = { @Sendable _ in
                print("AsyncStream for entity updates terminated.")
                
                // Ensure network resources are cleaned up
                self.stopListening()
            }
        }
    }
    
    func startListening() {
        do {
            listener = try NWListener(using: .tcp, on: port)
            listener?.stateUpdateHandler = { state in
                switch state {
                    case .ready:
                        self.statusMessage = "Listening on port \(self.port)"
                        print("Vision Pro listening on port \(self.port)")
                    case .failed(let error):
                        self.statusMessage = "Listener failed: \(error.localizedDescription)"
                        print("Listener failed with error: \(error)")
                        
                        // Finish stream on listener failure
                        self.entityUpdateContinuation?.finish()
                    case .cancelled:
                        self.statusMessage = "Listener cancelled"
                        print("Listener cancelled")
                        
                        // Finish stream on cancellation
                        self.entityUpdateContinuation?.finish()
                    default:
                        break
                }
            }
            
            listener?.newConnectionHandler = { [weak self] newConnection in
                guard let self = self else { return }
                print("New connection established from Blender!")
                self.statusMessage = "Connected to Blender"
                self.connection = newConnection
                self.connection?.start(queue: .main)
                self.receiveData()
            }
            
            listener?.start(queue: .main)
        } catch {
            self.statusMessage = "Failed to create listener: \(error.localizedDescription)"
            print("Failed to create listener: \(error)")
            
            // Finish stream on setup failure
            self.entityUpdateContinuation?.finish()
        }
    }
    
    private func receiveData() {
        connection?.receive(minimumIncompleteLength: 4, maximumLength: 4) { [weak self] (content, contentContext, isComplete, error) in
            guard let self = self else { return }
            
            if let content = content, !content.isEmpty {
                let dataLength = content.withUnsafeBytes { $0.load(as: UInt32.self).bigEndian }
                
                print("Receiving USDZ data of size: \(dataLength) bytes")
                self.statusMessage = "Receiving USDZ: \(dataLength / 1024) KB"
                
                self.connection?.receive(minimumIncompleteLength: Int(dataLength), maximumLength: Int(dataLength)) { (usdzContent, usdzContentContext, usdzIsComplete, usdzError) in
                    if let usdzContent = usdzContent, !usdzContent.isEmpty {
                        print("Received USDZ data. Size: \(usdzContent.count) bytes")
                        self.processData(usdzContent)
                    } else if let usdzError = usdzError {
                        self.statusMessage = "USDZ data receive error: \(usdzError.localizedDescription)"
                        print("Receive USDZ data error: \(usdzError)")
                        self.connection?.cancel()
                    } else if usdzIsComplete {
                        print("USDZ data stream finished unexpectedly (could be connection close).")
                        self.connection?.cancel()
                    } else {
                        print("USDZ data content was empty.")
                    }
                    self.receiveData()
                }
            } else if let error = error {
                self.statusMessage = "Connection receive error: \(error.localizedDescription)"
                print("Connection receive error: \(error)")
                self.connection?.cancel()
            } else if isComplete {
                self.statusMessage = "Connection closed by sender."
                print("Connection closed by sender.")
                self.connection?.cancel()
            } else {
                print("Received empty content.")
                self.receiveData()
            }
        }
    }
    
    private func processData(_ data: Data) {
        Task {
            do {
                let entity: Entity
                
                if #available(visionOS 26, *) {
                    entity = try await Entity(from: data)
                } else {
                    let tempFileURL = FileManager.default.temporaryDirectory.appendingPathComponent("received_scene_\(UUID().uuidString).usdz")
                    try data.write(to: tempFileURL)
                    entity = try await Entity(contentsOf: tempFileURL)
                    try FileManager.default.removeItem(at: tempFileURL)
                }
                
                // Switch to the MainActor and Updated status
                await MainActor.run {
                    print("USDZ loaded successfully into RealityKit!")
                    self.statusMessage = "USDZ Loaded: \(entity.name)"
                }
                
                // Yield the new entity to the AsyncStream
                entityUpdateContinuation?.yield(entity)
                
            } catch {
                // Switch to the MainActor for error status update
                await MainActor.run {
                    self.statusMessage = "Error loading USDZ: \(error.localizedDescription)"
                    print("Error processing USDZ data or loading into RealityKit: \(error)")
                }
            }
        }
    }
    
    func stopListening() {
        connection?.cancel()
        listener?.cancel()
        statusMessage = "Stopped listening."
        print("Stopped listening for Blender connections.")
        
        // Ensure stream is finished when stopping manually
        entityUpdateContinuation?.finish()
    }
}
