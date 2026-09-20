// posecheck — ဗီဒီယိုမှ **「ကင်မရာရှေ့ စကားပြောနေဟန်」** ကို frame အလိုက် တိုင်းသည်。
//
// Zin ၂၀၂၆-၀၉-၁၉: 「အမူအရာ ပုံမှန်မဟုတ်တဲ့ဟာ · စကားပြောနေတဲ့ပုံစံ မဟုတ်တဲ့
// transcript တွေ သုံးမရဘူးဆိုတာ မင်းကိုယ်တိုင် သိရမယ်」
// ⇒ အသံနဲ့ မရ · **ရုပ်ပုံကနေသာ** တိုင်းလို့ရသည်。
//
// သုံးပုံ:  ./posecheck <video> <fps> > out.jsonl
// ထွက်: frame တစ်ခုလျှင် JSON တစ်ကြောင်း —
//   t     စက္ကန့်
//   nf    မျက်နှာ အရေအတွက်
//   fa    အကြီးဆုံး မျက်နှာ ဧရိယာ (ဘောင်၏ အချိုး)
//   fx fy ၎င်း၏ အလယ် (0–1 · fy က အပေါ်မှ)
//   yaw   ဘယ်/ညာ လှည့် (ဒီဂရီ · macOS ပေးလျှင်)
//   roll  စောင်း (ဒီဂရီ)
//   ps    လူပုံ ဖုံးအုပ်မှု (ဘောင်၏ အချိုး) — လက် ကင်မရာ နားကပ်လျှင် တက်သည်
import CoreImage
import Foundation
import Vision
import AppKit

let a = CommandLine.arguments
guard a.count >= 3 else {
    FileHandle.standardError.write("usage: posecheck <framedir> <fps>\n".data(using:.utf8)!); exit(2)
}
// ⚠️ `AVAssetImageGenerator` ကို **မသုံးရ** — ဤ source မှာ ဗလာ ပုံသာ ပြန်ပေးပြီး
//    မျက်နှာ ၀ ခု · person ၀.၀၀၀ ဖြစ်ခဲ့သည် (၂၀၂၆-၀၉-၁၉ တကယ် ဖြစ်ခဲ့)。
//    ⇒ ffmpeg နဲ့ PNG ထုတ်ပြီး ဤကိရိယာက **ဖိုဒါကို** ဖတ်သည်。
let dir = a[1], fps = Double(a[2])!
let files = ((try? FileManager.default.contentsOfDirectory(atPath: dir)) ?? [])
              .filter { $0.hasSuffix(".png") }.sorted()
for (k, fn) in files.enumerated() {

    let t = Double(k) / fps
    guard let img = NSImage(contentsOfFile: (dir as NSString).appendingPathComponent(fn)),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { continue }

    // ── ① မျက်နှာ ──
    let fr = VNDetectFaceRectanglesRequest()
    try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([fr])
    let faces = (fr.results ?? [])
    var fa = 0.0, fx = -1.0, fy = -1.0, yaw = 999.0, roll = 999.0
    if let big = faces.max(by: { $0.boundingBox.width*$0.boundingBox.height
                               < $1.boundingBox.width*$1.boundingBox.height }) {
        let b = big.boundingBox
        fa = Double(b.width * b.height)
        fx = Double(b.midX)
        fy = 1.0 - Double(b.midY)          // အပေါ်မှ
        if let y = big.yaw  { yaw  = y.doubleValue * 180.0 / .pi }
        if let r = big.roll { roll = r.doubleValue * 180.0 / .pi }
    }

    // ── ② လူပုံ ဖုံးအုပ်မှု ──
    var ps = -1.0
    let sq = VNGeneratePersonSegmentationRequest()
    sq.qualityLevel = .fast
    sq.outputPixelFormat = kCVPixelFormatType_OneComponent8
    if (try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([sq])) != nil,
       let pb = (sq.results?.first as? VNPixelBufferObservation)?.pixelBuffer {
        CVPixelBufferLockBaseAddress(pb, .readOnly)
        let w = CVPixelBufferGetWidth(pb), hh = CVPixelBufferGetHeight(pb)
        let bpr = CVPixelBufferGetBytesPerRow(pb)
        if let base = CVPixelBufferGetBaseAddress(pb) {
            let p = base.assumingMemoryBound(to: UInt8.self)
            var on = 0
            // ⚠️ ၄ pixel ခြား နမူနာ — အားလုံး ရေတွက်လျှင် နှေးပြီး ရလဒ် မကွာ
            var yy = 0
            while yy < hh { var xx = 0
                while xx < w { if p[yy*bpr + xx] > 128 { on += 1 }; xx += 4 }
                yy += 4 }
            ps = Double(on) / Double((w/4) * (hh/4))
        }
        CVPixelBufferUnlockBaseAddress(pb, .readOnly)
    }
    print("{\"t\":\(String(format:"%.2f",t)),\"nf\":\(faces.count),"
        + "\"fa\":\(String(format:"%.5f",fa)),\"fx\":\(String(format:"%.3f",fx)),"
        + "\"fy\":\(String(format:"%.3f",fy)),\"yaw\":\(String(format:"%.1f",yaw)),"
        + "\"roll\":\(String(format:"%.1f",roll)),\"ps\":\(String(format:"%.4f",ps))}")
    fflush(stdout)
}
