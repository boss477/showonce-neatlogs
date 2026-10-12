"""Encrypted local secrets (.env.enc) using Windows DPAPI, falling back to a plain .env.

Only the Windows user who encrypted .env.enc can decrypt it, on the same machine.
Add or change a key without it appearing on screen or in shell history:

    python -m showonce.secrets set SLACK_BOT_TOKEN
    python -m showonce.secrets list
"""
import ctypes
import ctypes.wintypes as wt
import getpass
import os
import sys
from pathlib import Path
from dotenv import dotenv_values, load_dotenv

ENC_PATH = Path(".env.enc")

class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wt.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

def _dpapi(data: bytes, encrypt: bool) -> bytes:
    crypt32, kernel32 = ctypes.windll.crypt32, ctypes.windll.kernel32
    source, out = _Blob(len(data), ctypes.cast(ctypes.create_string_buffer(data, len(data)), ctypes.POINTER(ctypes.c_char))), _Blob()
    fn = crypt32.CryptProtectData if encrypt else crypt32.CryptUnprotectData
    if not fn(ctypes.byref(source), None, None, None, None, 0, ctypes.byref(out)):
        raise OSError("DPAPI failed: .env.enc was encrypted by another Windows user or machine")
    try: return ctypes.string_at(out.pbData, out.cbData)
    finally: kernel32.LocalFree(out.pbData)

def read() -> dict:
    if not ENC_PATH.exists(): return {}
    lines = _dpapi(ENC_PATH.read_bytes(), encrypt=False).decode().splitlines()
    return dict(line.split("=", 1) for line in lines if "=" in line)

def write(values: dict) -> None:
    ENC_PATH.write_bytes(_dpapi("\n".join(f"{k}={v}" for k, v in values.items()).encode(), encrypt=True))

def load() -> None:
    """Loads .env.enc into os.environ (existing env vars win), else a plain .env."""
    if ENC_PATH.exists() and os.name == "nt":
        for key, value in read().items(): os.environ.setdefault(key, value)
    else:
        load_dotenv()

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "list"
    values = read()
    if command == "set":
        key = sys.argv[2]
        value = getpass.getpass(f"{key} (input hidden): ").strip()
        if not value: sys.exit(f"{key} unchanged (empty input)")
        values = read(); values[key] = value  # re-read so a concurrent save isn't lost
        write(values); print(f"saved {key} to {ENC_PATH}")
    elif command == "import":  # encrypt an existing plain .env, then delete it
        values.update({k: v for k, v in dotenv_values(".env").items() if v})
        write(values); Path(".env").unlink(); print(f"encrypted .env into {ENC_PATH} and deleted the plain file")
    else:
        for key, value in sorted(values.items()): print(f"{key}: {'set' if value else 'EMPTY'}")
