import Foundation
import Vision
import AppKit

let inputFolder = URL(fileURLWithPath: CommandLine.arguments[1])
let outputFolder = URL(fileURLWithPath: CommandLine.arguments[2])
let files = try FileManager.default.contentsOfDirectory(at: inputFolder, includingPropertiesForKeys: nil)
    .filter { $0.pathExtension.lowercased() == "png" }
    .sorted { $0.lastPathComponent < $1.lastPathComponent }
var pageResults: [[String: Any]] = []
for (index, file) in files.enumerated() {
    // Preserve original PDF page numbers when only gap pages were rendered.
    let suffix = file.deletingPathExtension().lastPathComponent.split(separator: "-").last
    let physicalPage = suffix.flatMap { Int($0) } ?? (index + 1)
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["en-US"]
    request.usesLanguageCorrection = true
    let handler = VNImageRequestHandler(url: file, options: [:])
    try handler.perform([request])
    let observations = (request.results ?? []).sorted {
        if abs($0.boundingBox.midY - $1.boundingBox.midY) < 0.004 {
            return $0.boundingBox.minX < $1.boundingBox.minX
        }
        return $0.boundingBox.midY > $1.boundingBox.midY
    }
    let candidates = observations.compactMap { $0.topCandidates(1).first }
    let text = candidates.map { $0.string }.joined(separator: "\n") + "\n"
    let destination = outputFolder.appendingPathComponent(String(format: "page-%02d.txt", physicalPage))
    try text.write(to: destination, atomically: true, encoding: .utf8)
    let confidence = candidates.map { Double($0.confidence) }
    pageResults.append([
        "physical_page": physicalPage,
        "rendered_image": file.lastPathComponent,
        "characters": text.count,
        "recognized_lines": candidates.count,
        "mean_vision_confidence": confidence.isEmpty ? 0 : confidence.reduce(0,+) / Double(confidence.count),
        "minimum_vision_confidence": confidence.min() ?? 0
    ])
    print("Processed \(index + 1)/\(files.count), physical page \(physicalPage): \(text.count) characters")
    fflush(stdout)
}
let json = try JSONSerialization.data(withJSONObject: pageResults, options: [.prettyPrinted, .sortedKeys])
try json.write(to: outputFolder.appendingPathComponent("page-coverage.json"))
