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

@Observable
class BlenderSceneReceiver {
    @ObservationIgnored
    private var listener: NWListener?
    
    @ObservationIgnored
    private var connection: NWConnection?
    
    @ObservationIgnored
    private let port: NWEndpoint.Port
    
    // The AsyncStream to send Entity updates
    @ObservationIgnored
    private var entityUpdateContinuation: AsyncStream<Entity>.Continuation?
    public var sceneEntityUpdates: AsyncStream<Entity>! // Public stream for ContentView
    
    // Updates message to SwiftUI view
    var statusMessage: String = "Not listening"
    
    // Throttle status updates to prevent UI flickering
    @ObservationIgnored
    private var lastStatusUpdateTime: Date = .distantPast
    @ObservationIgnored
    private let statusUpdateInterval: TimeInterval = 5.0 // Update every 5 seconds
    
    // Internal method to update status with throttling
    private func updateStatus(_ message: String, force: Bool = false) {
        let now = Date()
        if force || now.timeIntervalSince(lastStatusUpdateTime) >= statusUpdateInterval {
            statusMessage = message
            lastStatusUpdateTime = now
        }
    }
    
    init(port: UInt16) {
        self.port = NWEndpoint.Port(rawValue: port)!
        
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
                        self.updateStatus("Listening on port \(self.port)", force: true)
                        print("Vision Pro listening on port \(self.port)")
                    case .failed(let error):
                        self.updateStatus("Listener failed: \(error.localizedDescription)", force: true)
                        print("Listener failed with error: \(error)")
                        
                        // Finish stream on listener failure
                        self.entityUpdateContinuation?.finish()
                    case .cancelled:
                        self.updateStatus("Listener cancelled", force: true)
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
                self.updateStatus("Connected to Blender", force: true)
                self.connection = newConnection
                self.connection?.start(queue: .main)
                self.receiveData()
            }
            
            listener?.start(queue: .main)
        } catch {
            updateStatus("Failed to create listener: \(error.localizedDescription)", force: true)
            print("Failed to create listener: \(error)")
            
            // Finish stream on setup failure
            entityUpdateContinuation?.finish()
        }
    }
    
    private func receiveData() {
        connection?.receive(minimumIncompleteLength: 4, maximumLength: 4) { [weak self] content, _, isComplete, error in
            guard let self = self else { return }
            
            if let content = content, !content.isEmpty {
                let dataLength = content.withUnsafeBytes { $0.load(as: UInt32.self).bigEndian }
                
                print("Receiving USDZ data of size: \(dataLength) bytes")
                self.updateStatus("Streaming: \(dataLength / 1024) KB")
                
                self.connection?.receive(minimumIncompleteLength: Int(dataLength), maximumLength: Int(dataLength)) { usdzContent, _, usdzIsComplete, usdzError in
                    if let usdzContent = usdzContent, !usdzContent.isEmpty {
                        print("Received USDZ data. Size: \(usdzContent.count) bytes")
                        self.processData(usdzContent)
                    } else if let usdzError = usdzError {
                        self.updateStatus("USDZ data receive error: \(usdzError.localizedDescription)", force: true)
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
                self.updateStatus("Connection receive error: \(error.localizedDescription)", force: true)
                print("Connection receive error: \(error)")
                self.connection?.cancel()
            } else if isComplete {
                self.updateStatus("Connection closed by sender.", force: true)
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
                    self.updateStatus("USDZ Loaded: \(entity.name)")
                }
                
                // Yield the new entity to the AsyncStream
                entityUpdateContinuation?.yield(entity)
                
            } catch {
                // Switch to the MainActor for error status update
                await MainActor.run {
                    self.updateStatus("Error loading USDZ: \(error.localizedDescription)", force: true)
                    print("Error processing USDZ data or loading into RealityKit: \(error)")
                }
            }
        }
    }
    
    func stopListening() {
        connection?.cancel()
        listener?.cancel()
        updateStatus("Stopped listening.", force: true)
        print("Stopped listening for Blender connections.")
        
        // Ensure stream is finished when stopping manually
        entityUpdateContinuation?.finish()
    }
}
