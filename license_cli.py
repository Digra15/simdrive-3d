#!/usr/bin/env python3
"""CLI lisensi SimDrive 3D. Contoh:
  ./license_cli.py new --count 5            # 5 kode permanen
  ./license_cli.py new --days 30 --count 1  # kode 30 hari
  ./license_cli.py list
  ./license_cli.py revoke 123456
  ./license_cli.py auto off
  ./license_cli.py stats
"""
import argparse, json, sys
import licensing


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("--count", type=int, default=1)
    n.add_argument("--days", type=int, default=0)
    n.add_argument("--note", default="")
    n.add_argument("--customer", default="")
    sub.add_parser("list")
    r = sub.add_parser("revoke")
    r.add_argument("code")
    a = sub.add_parser("auto")
    a.add_argument("state", choices=["on", "off"])
    sub.add_parser("stats")
    sub.add_parser("token")
    kg = sub.add_parser("keygen")
    kg.add_argument("device")
    args = ap.parse_args()

    if args.cmd == "keygen":
        print(licensing.keygen(args.device))
    elif args.cmd == "new":
        out = licensing.create_codes(args.count, args.days, args.note, args.customer)
        print(f"{'PERMANEN' if out['permanent'] else str(out['days']) + ' hari'} — {len(out['codes'])} kode:")
        for c in out["codes"]:
            print(" ", c)
    elif args.cmd == "list":
        for c in licensing.list_codes():
            state = "REVOKED" if c.get("revoked") else ("BOUND " + (c.get("deviceId") or "")[:12] if c.get("deviceId") else "free")
            masa = "lifetime" if c.get("permanent") else f"{c.get('days')}d exp={c.get('expiresAt')}"
            print(f"{c['code']}  {state:20} {masa:32} {c.get('customer','')} {c.get('note','')}")
    elif args.cmd == "revoke":
        print(json.dumps(licensing.revoke(args.code), ensure_ascii=False))
    elif args.cmd == "auto":
        print("auto =", licensing.set_auto(args.state == "on"))
    elif args.cmd == "stats":
        print(json.dumps(licensing.stats(), ensure_ascii=False))
    elif args.cmd == "token":
        print(licensing.token())


if __name__ == "__main__":
    sys.exit(main())
