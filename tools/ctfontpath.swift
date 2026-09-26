// Which FILE does CoreText actually load for a PostScript name?
// R-G3 (Zin, 2026-09-26): with several files installed under one name
// (Pyidaungsu has four), recording all their hashes proves nothing — CoreText
// could switch from one to another without any hash changing.  This asks
// CoreText itself: CTFontCreateWithName → kCTFontURLAttribute.
// Read-only: prints one JSON line per name; touches no font file.
import Foundation
import CoreText

for name in CommandLine.arguments.dropFirst() {
    let f = CTFontCreateWithName(name as CFString, 120, nil)
    let url = CTFontCopyAttribute(f, kCTFontURLAttribute) as? URL
    let ps = CTFontCopyPostScriptName(f) as String
    let obj: [String: Any] = ["asked": name, "resolved_ps": ps,
                              "file": url?.path ?? "",
                              "substituted": ps != name]
    let d = try! JSONSerialization.data(withJSONObject: obj)
    print(String(data: d, encoding: .utf8)!)
}
