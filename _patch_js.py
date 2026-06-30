import io

f = r"C:\Users\shjaisw\.kiro\Claude kiro\ai-agency-platform\backend\static\js\video_creator.js"
with io.open(f, "r", encoding="utf-8") as fp:
    c = fp.read()

old = (
    '    }else{\n'
    '      ov2.innerHTML=\'<div style="background:#1e293b;border-radius:16px;padding:20px;max-width:280px;width:90%;text-align:center"><p style="color:#ef4444;font-weight:600">Failed</p><p style="font-size:.72rem;color:#94a3b8;margin:8px 0">\'+(d.message||"Try again")+\'</p><button onclick="this.parentNode.parentNode.remove()" style="padding:8px 16px;background:#334155;border:none;border-radius:8px;color:#fff;cursor:pointer">Close</button></div>\';\n'
    '    }'
)

new = (
    '    }else{\n'
    '      var msg=d.detail||d.message||"Try again";\n'
    '      var buy=/credit|Rs\\.5/i.test(msg)?\'<a href="/api/panel/\'+window._wid+\'" style="display:block;margin-top:10px;padding:10px;background:#6366f1;border-radius:8px;color:#fff;text-decoration:none;font-weight:700">Buy Credits</a>\':"";\n'
    '      ov2.innerHTML=\'<div style="background:#1e293b;border-radius:16px;padding:20px;max-width:280px;width:90%;text-align:center"><p style="color:#f59e0b;font-weight:600">Action needed</p><p style="font-size:.72rem;color:#94a3b8;margin:8px 0">\'+msg+\'</p>\'+buy+\'<button onclick="this.parentNode.parentNode.remove()" style="margin-top:8px;padding:8px 16px;background:#334155;border:none;border-radius:8px;color:#fff;cursor:pointer">Close</button></div>\';\n'
    '    }'
)

if old in c:
    c = c.replace(old, new)
    with io.open(f, "w", encoding="utf-8", newline="") as fp:
        fp.write(c)
    print("PATCHED")
else:
    print("OLD NOT FOUND")
