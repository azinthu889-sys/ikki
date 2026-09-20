// textcov — ဖန်သားပြင်ပေါ် **စာသား/ဂရပ်ဖစ် ဖုံးအုပ်မှု**ကို frame အလိုက် တိုင်းသည်。
//
// ⚠️ style တစ်ခုကို ဆောက်ဖို့ 「effect ဘယ်လောက် များလဲ」 ကို **မှန်းဆ၍ မရ** —
//    reference ဗီဒီယိုမှ တိုင်းရသည်。 macOS Vision ရဲ့ စာသား ရှာချက်ကို သုံးသည်
//    (ML model ထပ်သွင်းစရာ မလို)。
//
// သုံးပုံ:  ./textcov <framedir> <fps>
// ထွက်: frame တစ်ခုလျှင် JSON — t · n (စာသား အကွက်) · cov (ဘောင်၏ အချိုး) ·
//        top/mid/bot (အပေါ်/အလယ်/အောက် အပိုင်းအလိုက် အကွက် အရေအတွက်)
import Foundation
import Vision
import AppKit

let a = CommandLine.arguments
guard a.count >= 3 else {
    FileHandle.standardError.write("usage: textcov <framedir> <fps>\n".data(using:.utf8)!); exit(2)
}
let dir = a[1], fps = Double(a[2])!
let files = ((try? FileManager.default.contentsOfDirectory(atPath: dir)) ?? [])
              .filter { $0.hasSuffix(".png") }.sorted()

for (k, fn) in files.enumerated() {
    let t = Double(k) / fps
    guard let img = NSImage(contentsOfFile: (dir as NSString).appendingPathComponent(fn)),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { continue }
    let rq = VNRecognizeTextRequest()
    rq.recognitionLevel = .fast
    rq.usesLanguageCorrection = false
    try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([rq])
    let obs = (rq.results ?? [])
    var cov = 0.0, top = 0, mid = 0, bot = 0
    for o in obs {
        let b = o.boundingBox            // normalised, origin bottom-left
        cov += Double(b.width * b.height)
        let cy = 1.0 - Double(b.midY)    // အပေါ်မှ
        if cy < 0.33 { top += 1 } else if cy < 0.67 { mid += 1 } else { bot += 1 }
    }
    print("{\"t\":\(String(format:"%.2f",t)),\"n\":\(obs.count),"
        + "\"cov\":\(String(format:"%.5f",cov)),"
        + "\"top\":\(top),\"mid\":\(mid),\"bot\":\(bot)}")
    fflush(stdout)
}
