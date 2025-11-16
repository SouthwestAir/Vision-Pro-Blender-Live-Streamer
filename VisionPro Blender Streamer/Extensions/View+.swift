//
//  View+.swift
//  VisionPro Blender Streamer
//
//  Created by Juan Alejandro Moya Grajales on 16/11/2025.
//

import Foundation
import SwiftUI

extension View {
    func debugBorder3D(_ color: Color) -> some View {
        spatialOverlay {
            ZStack {
                Color.clear.border(color, width: 2)
                ZStack {
                    Color.clear.border(color, width: 2)
                    Spacer()
                    Color.clear.border(color, width: 2)
                }
                .rotation3DLayout(.degrees(90), axis: .y)
                Color.clear.border(color, width: 2)
            }
        }
    }
}
