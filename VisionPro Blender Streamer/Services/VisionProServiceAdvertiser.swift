//
//  VisionProServiceAdvertiser.swift
//  VisionPro Blender Streamer
//
//  Created by Justin Leger on 6/22/25.
//


import Foundation
import Network

class VisionProServiceAdvertiser: NSObject, NetServiceDelegate {
    var netService: NetService?
    let serviceDomain = "local." // These match the Blender Python script variable: service_domain
    let serviceType = "_visionpro_blender._tcp." // These match the Blender Python script variable: service_type
    let servicePort: Int32 = 8080 // MUST match Blender's connection port
    
    func startAdvertising() {
        netService = NetService(domain: serviceDomain, type: serviceType, name: "MyVisionPro", port: servicePort)
        netService?.delegate = self
        netService?.includesPeerToPeer = true // For direct device discovery
        netService?.publish()
        print("Advertising Bonjour service: \(serviceType) on port \(servicePort)")
    }
    
    func netServiceDidPublish(_ sender: NetService) {
        print("Bonjour service published: \(sender.name).local.:\(sender.port)")
    }
    
    func netService(_ sender: NetService, didNotPublish errorDict: [String : NSNumber]) {
        print("Failed to publish Bonjour service: \(errorDict)")
    }
    
    func stopAdvertising() {
        netService?.stop()
        netService = nil
        print("Stopped Bonjour advertising.")
    }
}
