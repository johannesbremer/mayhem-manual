#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import argparse
import hashlib
import html
import mimetypes
import re
import unicodedata

parser = argparse.ArgumentParser()
parser.add_argument("--wiki-root", default=".", help="Path to the cloned wiki checkout")
parser.add_argument("--out-dir", default="build/pdf", help="Directory for generated PDF sources")
args = parser.parse_args()

ROOT = Path(args.wiki_root).resolve()
OUT = Path(args.out_dir).resolve()
REMOTE_IMAGES = OUT / "remote-images"
failed_remote_images = []

OUT.mkdir(parents=True, exist_ok=True)

REQUESTED = [
    ("Repairs", [
        "Replace AMP",
        "SMD buttons and caps",
        "Encoder knob",
        "SMA Connector replacement or removal",
    ]),
    ("Manual", [
        "Intended use and Legality",
        "Usage cautions",
        "First steps",
        "About firmwares",
        "Redirections on this manual/project",
        "Firmware update procedure",
        "Flash Mayhem onto bare HackRF",
        "Updating the Xilinx CPLD on hackrf board",
        "User interface",
        "Splash screen",
        "Title bar",
        "Main menu",
        "Main Controls",
        "SD Card content and modification",
        "Text Entry",
        "Powering the PortaPack",
        "Troubleshooting",
        "Won't boot",
        "Config Menu",
        "Firmware upgrade",
        "Diagnose firmware update in Windows",
        "Receive Quality Issues",
        "No TX/RX",
        "TX Carrier Only",
        "H2+ speaker modifications",
        "Dead Coin Cell Battery",
        "Factory Defaults",
        "SD card not recognized by PC with the SD-card over USB selected",
        "DFU overlay",
        "Full reset",
        "SolveBoard",
        "How to Format SDCard",
        "What if I don't like some of the apps",
    ]),
    ("Applications", [
        "Applications",
        "Receivers",
        "2-Tone-RX",
        "ACARS",
        "ADS-B",
        "AFSK",
        "AIS Boats",
        "Analog TV",
        "APRS RX",
        "Audio",
        "BLE RX",
        "Detector",
        "EPIRB RX",
        "ERT Meter",
        "Flex RX",
        "Radio",
        "Fox-Hunt",
        "FPV-Detect",
        "gfxEQ",
        "Level",
        "Morse RX",
        "NOAA",
        "NRF",
        "POCSAG",
        "ProtoView",
        "Radiosonde",
        "RTTY RX",
        "Scanner",
        "Search",
        "SSTV RX",
        "SubCar",
        "SubGhzD",
        "Time Sink",
        "TPMS RX",
        "Weather",
        "WeFax",
        "Transmitters",
        "2-Tone-TX",
        "ADS-B(S) TX",
        "Adult Toys",
        "APRS TX",
        "BHT Xy/EP",
        "BLE TX",
        "BLESpam",
        "Burger Pager",
        "CVS Spam",
        "EPIRB",
        "Flex TX",
        "FlipperTX",
        "GPS Sim",
        "Hopper",
        "Jammer",
        "KeeLoq TX",
        "Key fob TX",
        "LGE Tool",
        "MDC-1200 TX",
        "Morse TX",
        "OOK",
        "OOK Brute",
        "OOK Editor",
        "P25 TX",
        "POCSAG TX",
        "RDS",
        "RTTY TX",
        "SAME TX",
        "Signal gen",
        "Soundboard",
        "Spectrum Painter",
        "SSTV",
        "TEDI/LCR",
        "TouchTunes",
        "TPMS TX",
        "Transceivers",
        "Microphone Transceiver",
        "KISS TNC",
        "Recon",
        "Capture",
        "C16 Format",
        "Replay",
        "Remote",
        "Looking Glass",
        "Utilities",
        "Antenna length",
        "Calculator",
        "Cart Lock",
        "Debug Menu",
        "File manager",
        "Flash Utility",
        "Freq manager",
        "IQ Trim",
        "Metronome",
        "Notepad",
        "Playlist Editor",
        "Rand Pwd",
        "SD over USB",
        "Stopwatch",
        "Tuner",
        "WardriveMap",
        "Waterfall Designer",
        "Wav Viewer",
        "Wipe SD card",
        "Games",
        "Battleship",
        "Blackjack",
        "Breakout",
        "2048",
        "Digital Rain",
        "Dino Game",
        "Doom",
        "Morse P",
        "Pac-Man",
        "Snake",
        "Space Invaders",
        "Tetris",
        "Settings",
        "HackRF Mode",
    ]),
]

ALIASES = {
    "Replace AMP": "Preamplifier-IC-replacement.md",
    "SMD buttons and caps": "Push-buttons-and-button-caps.md",
    "Encoder knob": "Encoder.md",
    "SMA Connector replacement or removal": "SMA-connector-replacement-or-removal.md",
    "Redirections on this manual/project": "Redirections.md",
    "Firmware update procedure": "Update-firmware.md",
    "Firmware upgrade": "Update-firmware-troubleshooting.md",
    "Splash screen": "Splash-and-other-images.md",
    "SD Card content and modification": "SD-Card-Content.md",
    "Receive Quality Issues": "Help!-Im-not-receiving-anything!---Receive-Quality-Issues.md",
    "ADS-B": "Automatic-dependent-surveillance–broadcast-(ADS-B).md",
    "Audio": "Audio-Receivers.md",
    "BLE RX": "Bluetooth-Low-Energy-Receiver.md",
    "EPIRB": "EPIRB-TX.md",
    "ERT Meter": "ERT.md",
    "NRF": "Decoder-for-NRF24L01.md",
    "POCSAG": "POCSAG-Receiver.md",
    "WeFax": "WeatherFax.md",
    "ADS-B(S) TX": "ADS-B(S).md",
    "BLE TX": "Bluetooth-Low-Energy-Transmitter.md",
    "BHT Xy/EP": "BHT.md",
    "Flex TX": "FLEX-TX.md",
    "Signal gen": "Signal-Generator.md",
    "TEDI/LCR": "LCR.md",
    "Antenna length": "Antennas.md",
    "Debug Menu": "Debug.md",
    "Rand Pwd": "Random-password.md",
    "Pac-Man": "Pac‐Man.md",
    "HackRF Mode": "HackRF.md",
}

SECTION_ONLY = {
    "Applications",
    "Receivers",
    "Transmitters",
    "Transceivers",
    "Utilities",
    "Games",
    "Settings",
}

def slug(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", text.lower())

files = {p.name: p for p in ROOT.glob("*.md") if not p.name.startswith("_")}
by_slug = {slug(p.stem): p.name for p in files.values()}

def resolve(title):
    if title in ALIASES:
        return ALIASES[title] if (ROOT / ALIASES[title]).exists() else None
    direct = title.replace(" ", "-") + ".md"
    if direct in files:
        return direct
    return by_slug.get(slug(title))

def image_extension(url, content_type):
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}:
        return suffix
    if content_type:
        guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if guessed:
            return ".jpg" if guessed == ".jpe" else guessed
    return ".img"

def cache_remote_image(url):
    REMOTE_IMAGES.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    existing = sorted(REMOTE_IMAGES.glob(f"{key}.*"))
    if existing:
        return existing[0].relative_to(OUT).as_posix()

    request = Request(url, headers={"User-Agent": "mayhem-wiki-pdf-builder/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            data = response.read()
            content_type = response.headers.get("content-type", "")
    except Exception as exc:
        failed_remote_images.append(f"{url} - {exc}")
        return None
    ext = image_extension(url, content_type)
    path = REMOTE_IMAGES / f"{key}{ext}"
    path.write_bytes(data)
    return path.relative_to(OUT).as_posix()

def cache_remote_images(text):
    def markdown_image(match):
        alt, url = match.group(1), match.group(2)
        path = cache_remote_image(url)
        return f"![{alt}]({path})" if path else f"[{alt or 'image'}]({url})"

    def image_link(match):
        label, url = match.group(1), match.group(2)
        if "image" not in label.lower():
            return match.group(0)
        path = cache_remote_image(url)
        return f"![{label}]({path})" if path else match.group(0)

    def html_image(match):
        attrs = match.group(1)
        src = re.search(r"""src=["'](https?://[^"']+)["']""", attrs)
        alt = re.search(r"""alt=["']([^"']*)["']""", attrs)
        if not src:
            return match.group(0)
        path = cache_remote_image(src.group(1))
        return f"![{alt.group(1) if alt else 'image'}]({path})" if path else match.group(0)

    text = re.sub(r"<img\b([^>]*)>", html_image, text, flags=re.IGNORECASE)
    text = re.sub(r"!\[([^\]]*)\]\((https?://[^)]+)\)", markdown_image, text)
    text = re.sub(r"\[([^\]]*image[^\]]*)\]\((https?://[^)]+)\)", image_link, text, flags=re.IGNORECASE)
    return text

def strip_github_alerts(text):
    text = re.sub(r"^> \[!(\w+)\]\s*$", r"> **\1**", text, flags=re.MULTILINE)
    text = text.replace("- / (root) folder", "- `/` (root) folder")
    text = text.replace("https://github.com/portapack-mayhem/mayhem-firmware/wiki/img/", "../../img/")
    text = text.replace("/portapack-mayhem/mayhem-firmware/wiki/img/", "img/")
    text = re.sub(r"(!\[[^\]]*\]\()img/", r"\1../../img/", text)
    text = re.sub(r"\[!\[([^\]]*)\]\([^)]+\)\]\((https?://[^)]+)\)", r"[\1](\2)", text)
    text = cache_remote_images(text)
    text = re.sub(r"(?<!!)\[([^\]]+)\]\((?!(?:https?://|mailto:))[^)]+\)", r"\1", text)
    text = re.sub(r"(?<=\w) / (?=\w)", " or ", text)
    text = text.replace("![alt](url)", "`![alt](url)`")
    return text

def split_table_row(line):
    line = line.strip()
    if not line.startswith("|") or not line.endswith("|"):
        return None
    return [part.strip() for part in line.strip("|").split("|")]

def plain_text(text):
    text = html.unescape(text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*\*([^*]*)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]*)\*", r"\1", text)
    text = re.sub(r"(?<!!)\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.replace("<br>", " ").replace("<br />", " ").strip()

def convert_pipe_tables(text):
    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        header = split_table_row(lines[i])
        sep = split_table_row(lines[i + 1]) if i + 1 < len(lines) else None
        if header and sep and all(re.fullmatch(r":?-{3,}:?", cell) for cell in sep):
            rows = []
            i += 2
            while i < len(lines):
                row = split_table_row(lines[i])
                if not row:
                    break
                rows.append(row)
                i += 1
            if header[:2] == ["Problem", "Solution"]:
                for row in rows:
                    if len(row) < 2:
                        continue
                    problem, solution = row[0], row[1]
                    solution = solution.replace("<br />", "\n  ")
                    out += [f"### {problem}", "", solution, ""]
            else:
                for row in rows:
                    values = row + [""] * (len(header) - len(row))
                    pairs = [
                        f"{plain_text(column)}: {plain_text(value)}"
                        for column, value in zip(header, values)
                        if column and value
                    ]
                    if pairs:
                        out.append("- " + "; ".join(pairs))
                out.append("")
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)

used = set()
missing = []
combined = [
    "---",
    "title: Mayhem Firmware Manual",
    "subtitle: Selected wiki export",
    "toc: true",
    "---",
    "",
]

for section, titles in REQUESTED:
    combined += [f"# {section}", ""]
    for title in titles:
        name = resolve(title)
        if title in SECTION_ONLY:
            combined += [f"## {title}", ""]
            continue
        if not name:
            missing.append(f"{section}: {title}")
            continue
        if name in used:
            continue
        used.add(name)
        text = (ROOT / name).read_text(encoding="utf-8")
        text = strip_github_alerts(text)
        text = convert_pipe_tables(text)
        combined += [f"## {title}", "", f"<!-- source: {name} -->", "", text.strip(), ""]

(OUT / "mayhem-manual-combined.md").write_text("\n".join(combined), encoding="utf-8")
(OUT / "missing-pages.txt").write_text("\n".join(missing) + ("\n" if missing else ""), encoding="utf-8")
(OUT / "failed-remote-images.txt").write_text(
    "\n".join(failed_remote_images) + ("\n" if failed_remote_images else ""),
    encoding="utf-8",
)
