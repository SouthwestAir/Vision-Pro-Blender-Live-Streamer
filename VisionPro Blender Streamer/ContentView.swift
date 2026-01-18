//
//  ContentView.swift
//  VisionPro Blender Streamer
//
//  Created by Justin Leger on 6/23/25.
//

import RealityKit
import RealityKitContent
import SwiftUI

struct ContentView: View {
    @Environment(AppModel.self) private var appModel

    var body: some View {
        VStack(spacing: 20) {
            // App Title
            Text("Vision Pro Blender Streamer")
                .font(.largeTitle)
                .fontWeight(.bold)
            
            // 3D Scene Preview
            Model3D(named: "Scene", bundle: realityKitContentBundle)
                .frame(height: 200)
                .padding(.bottom, 10)
            
            // Status Card
            VStack(spacing: 12) {
                HStack {
                    Image(systemName: appModel.isConnected ? "antenna.radiowaves.left.and.right" : "antenna.radiowaves.left.and.right.slash")
                        .foregroundStyle(appModel.isConnected ? .green : .secondary)
                        .font(.title2)
                    
                    Text("Connection Status")
                        .font(.headline)
                    
                    Spacer()
                }
                
                Text(appModel.receiver.statusMessage)
                    .font(.body)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding()
                    .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
            }
            .padding()
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
            
            Spacer()
            
            // Immersive Space Toggle
            ToggleImmersiveSpaceButton()
                .padding(.bottom, 20)
        }
        .padding(30)
        .onAppear {
            // Start services when app launches
            appModel.advertiser.startAdvertising()
            appModel.receiver.startListening()
        }
    }
}

#Preview(windowStyle: .automatic) {
    ContentView()
        .environment(AppModel())
}
