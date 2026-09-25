// mouthcheck — frame တစ်ခုချင်းရဲ့ **နှုတ်ခမ်း ဟမှု** (အကြီးဆုံး မျက်နှာ)。
//
// podcast ပုံစံ တိုင်းရန် — 「ပြသထားသူက စကားပြောနေလား၊ နားထောင်နေလား」。
// အသံ cluster (MFCC k-means) က ၅၇/၄၃ သာ ခွဲနိုင်ခဲ့ ⇒ ရုပ်ပုံကနေ တိုင်းသည်。
//
// သုံးပုံ:  ./mouthcheck <framedir>  > out.jsonl
// ထွက်: {"f": ဖိုင်နာမည်, "nf": မျက်နှာ, "fa": မျက်နှာ ဧရိယာ,
//        "fx": အလယ် x, "open": အတွင်းနှုတ်ခမ်း အမြင့် ÷ အကျယ်}
// ⚠️ ဖိုဒါကို ဖတ်သည် — AVAssetImageGenerator က ဗလာ ပုံ ပြန်ပေးခဲ့ (posecheck.swift)。
import AppKit
import Foundation
import Vision

let a = CommandLine.arguments
guard a.count >= 2 else {
    FileHandle.standardError.write("usage: mouthcheck <framedir>\n".data(using: .utf8)!); exit(2)
}
let dir = a[1]
let files = ((try? FileManager.default.contentsOfDirectory(atPath: dir)) ?? [])
    .filter { $0.hasSuffix(".jpg") || $0.hasSuffix(".png") }.sorted()

func span(_ pts: [CGPoint]) -> (CGFloat, CGFloat) {
    let xs = pts.map { $0.x }, ys = pts.map { $0.y }
    return ((xs.max() ?? 0) - (xs.min() ?? 0), (ys.max() ?? 0) - (ys.min() ?? 0))
}

for fn in files {
    guard let img = NSImage(contentsOfFile: (dir as NSString).appendingPathComponent(fn)),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { continue }
    let rq = VNDetectFaceLandmarksRequest()
    try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([rq])
    let faces = (rq.results ?? []).sorted {
        $0.boundingBox.width * $0.boundingBox.height > $1.boundingBox.width * $1.boundingBox.height }
    var open = -1.0, fa = 0.0, fx = -1.0
    if let f = faces.first {
        fa = Double(f.boundingBox.width * f.boundingBox.height)
        fx = Double(f.boundingBox.midX)
        if let lip = f.landmarks?.innerLips, lip.pointCount > 2 {
            let (w, h) = span(lip.normalizedPoints)
            if w > 0 { open = Double(h / w) }
        }
    }
    print(String(format: "{\"f\":\"%@\",\"nf\":%d,\"fa\":%.4f,\"fx\":%.3f,\"open\":%.4f}",
                 fn, faces.count, fa, fx, open))
}
