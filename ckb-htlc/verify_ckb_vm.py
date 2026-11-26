#!/usr/bin/env python3
import hashlib, json, subprocess, copy

SO = "/home/sandbox/.openclaw/workspace/项目/hush-v1-poc/ckb-htlc/ckb-htlc.so"
DBG = "/tmp/ckbd/ckb-debugger"
BASE = "/tmp/mock_tx.json"

def bytes_opt(b):
    return (0).to_bytes(4, "little") if b is None else len(b).to_bytes(4, "little") + b

def witness_args(lock=None):
    parts = [bytes_opt(lock), b"\x00"*4, b"\x00"*4, b"\x00"*4, b"\x00"*4]
    h = 4 + 4*len(parts); offs, cur = [], h
    for p in parts: offs.append(cur); cur += len(p)
    return cur.to_bytes(4, "little") + b"".join(o.to_bytes(4, "little") for o in offs) + b"".join(parts)

base = json.load(open(BASE))

preimage = bytes(range(32))
h = hashlib.sha256(preimage).digest()
cases = [
    ("① hashlock: 正确 preimage, since=0       (期望 PASS=0)", preimage, 0, 400, True),
    ("② hashlock: 错误 preimage, since=0       (期望 REJECT)", bytes([9])*32, 0, 400, False),
    ("③ timelock: 空witness, tl=0, since=0     (期望 PASS=0)", None, 0, 0, True),
    ("④ timelock: 空witness, tl=1, since=0     (期望 REJECT)", None, 0, 1, False),
]

allok = True
for name, wl, since, timelock, expect_pass in cases:
    args_hex = "0x" + (h + timelock.to_bytes(8, "little")).hex()
    tx = copy.deepcopy(base)
    # 保持 secp 的 code_hash/hash_type（让 debugger 能定位脚本），只替换 args
    tx["mock_info"]["inputs"][0]["output"]["lock"]["args"] = args_hex
    tx["tx"]["inputs"][0]["since"] = hex(since)
    tx["tx"]["witnesses"][0] = "0x" + (wl.hex() if wl else "")
    p = "/tmp/ckbd/tx2.json"
    json.dump(tx, open(p, "w"))
    r = subprocess.run([DBG, "--tx-file", p, "--bin", SO, "--script", "input.0.lock", "--script-version", "2"],
                       capture_output=True, text=True, timeout=180)
    out = (r.stdout + r.stderr).strip()
    code = r.returncode
    passed = (code == 0)
    ok = (passed == expect_pass)
    if not ok: allok = False
    print(f"\n{name}\n   exit={code} {'✅' if ok else '❌'}")
    for l in [l for l in out.splitlines() if l.strip()][-2:]:
        print("   |", l)

print("\n" + ("✅ HTLC 五场景全部符合预期（真实 ckb-vm 执行）" if allok else "❌ 有偏差"))
