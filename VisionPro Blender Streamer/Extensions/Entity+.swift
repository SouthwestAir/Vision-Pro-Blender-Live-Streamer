//
//  Entity+.swift
//  VisionPro Blender Streamer
//
//  Created by Juan Alejandro Moya Grajales on 16/11/2025.
//

import Foundation
import RealityKit
import SwiftUI

extension Entity {

    @MainActor func scaleWithVolume(
        _ realityViewContent: RealityViewContent,
        _ geometryProxy3D: GeometryProxy3D,
        _ defaultVolumeSize: Size3D = Size3D(width: 1, height: 1, depth: 1)
    ) {

        let scaledVolumeContentBoundingBox = realityViewContent.convert(geometryProxy3D.frame(in: .local), from: .local, to: .scene)

        let scaleX = scaledVolumeContentBoundingBox.extents.x / Float(defaultVolumeSize.width)
        let scaleY = scaledVolumeContentBoundingBox.extents.y / Float(defaultVolumeSize.height)
        let scaleZ = scaledVolumeContentBoundingBox.extents.z / Float(defaultVolumeSize.depth)

        let newScale: SIMD3<Float> = [scaleX, scaleY, scaleZ]
        self.scale = newScale

    }
}
