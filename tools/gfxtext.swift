// gfxtext — ပုံတစ်ခုချင်းမှာ **စာသား တကယ် ပေါ်မပေါ်** နှင့် **ဘောင်ပြင် ထွက်မထွက်**
//           ကို စစ်သည် (macOS Vision)。
//
// ⚠️ ဘာကြောင့် လိုလဲ — ၂၀၂၆-၀၉-၂၀: template စစ်ချက်က `alpha` ဖုံးအုပ်မှုပဲ
//    တိုင်းထားသဖြင့် **အရောင်တုံးကြီး ချည်းပဲ ပါပြီး စာသား လုံးဝ မပါသော**
//    template များ (infogfx.pyramid · prem.glass_stat · titles.label_pill)
//    အောင်သွားခဲ့သည်。 Zin: 「template သုံးထားတာတွေရော quality 0」。
//
// သုံးပုံ:  ./gfxtext <png> [<png> …]
// ထွက်:   ဖိုင်တစ်ခုလျှင် JSON — n (စာသား အကွက်) · cov · edge (အနားနဲ့ အနီးဆုံး
//         အချိုး) · txt (တွေ့သော စာသား)
import Foundation
import Vision
import AppKit

let args = Array(CommandLine.arguments.dropFirst())
guard !args.isEmpty else {
    FileHandle.standardError.write("usage: gfxtext <png> …\n".data(using:.utf8)!); exit(2)
}
func esc(_ s: String) -> String {
    var o = ""
    for c in s.unicodeScalars {
        switch c {
        case "\"": o += "\\\""
        case "\\": o += "\\\\"
        case "\n", "\r", "\t": o += " "
        default:
            if c.value < 0x20 { o += " " } else { o.unicodeScalars.append(c) }
        }
    }
    return o
}
for path in args {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        print("{\"f\":\"\(esc(path))\",\"n\":-1,\"why\":\"ဖတ်မရ\"}"); continue
    }
    let rq = VNRecognizeTextRequest()
    // ⚠️ `.accurate` သုံးရသည် — `.fast` က မြန်မာစာကို လွတ်တတ်သည်。
    rq.recognitionLevel = .accurate
    rq.usesLanguageCorrection = false
    try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([rq])
    let obs = rq.results ?? []
    var cov = 0.0
    var edge = 1.0                      // အနားနဲ့ အနီးဆုံး (၀ = ကပ်နေ)
    var txt: [String] = []
    for o in obs {
        let b = o.boundingBox           // normalised · origin bottom-left
        cov += Double(b.width * b.height)
        edge = min(edge, Double(min(b.minX, b.minY, 1 - b.maxX, 1 - b.maxY)))
        if let t = o.topCandidates(1).first?.string { txt.append(t) }
    }
    if obs.isEmpty { edge = -1 }
    let j = txt.prefix(4).map { "\"\(esc($0))\"" }.joined(separator: ",")
    print("{\"f\":\"\(esc((path as NSString).lastPathComponent))\",\"n\":\(obs.count),"
        + "\"cov\":\(String(format:"%.5f",cov)),"
        + "\"edge\":\(String(format:"%.4f",edge)),\"txt\":[\(j)]}")
    fflush(stdout)
}
