#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import posixpath
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from bs4 import BeautifulSoup


ENTRY_MAP = {
    "gept-hi-second-stage-integrated-handout.html": "ethan-gept-writing-speaking.html",
    "today-topic-white-lies-gsat-gept-context-lab.html": "ethan-white-lies-writing-speaking-context-lab.html",
    "gept-high-intermediate-second-stage-materials.html": "ethan-gept-second-stage-materials.html",
}

ENTRY_SOURCES = tuple(ENTRY_MAP.keys())
MAX_PAGES_FILE_MB = 95
RELEASE_TAG = "b132-source-assets-2026-06-29"
RELEASE_BASE = "https://github.com/b13102033-svg/b132-public-handouts/releases/download"
ALWAYS_INCLUDE_HTML = {
    "today-topic-white-lies-open-resource-library.html",
    "today-topic-white-lies-tact-vs-honesty.html",
}


@dataclass(frozen=True)
class RefParts:
    raw: str
    path: str
    query: str
    fragment: str


def parse_ref(value: str | None) -> RefParts | None:
    if not value:
        return None
    value = value.strip()
    if (
        not value
        or value.startswith("#")
        or value.startswith("http://")
        or value.startswith("https://")
        or value.startswith("mailto:")
        or value.startswith("tel:")
        or value.startswith("javascript:")
        or value.startswith("data:")
    ):
        return None
    split = urlsplit(value)
    if not split.path:
        return None
    return RefParts(value, unquote(split.path), split.query, split.fragment)


def with_suffix_url(path: str, query: str, fragment: str) -> str:
    return urlunsplit(("", "", path, query, fragment))


def normalize_rel(path: Path, root: Path) -> str | None:
    path_norm = Path(os.path.normpath(os.fspath(path.absolute())))
    root_norm = Path(os.path.normpath(os.fspath(root.absolute())))
    try:
        return path_norm.relative_to(root_norm).as_posix()
    except ValueError:
        return None


def resolve_local_ref(local_viewer: Path, html_rel: str, ref_path: str) -> str | None:
    base = (local_viewer / html_rel).parent
    return normalize_rel(base / ref_path, local_viewer)


def public_html_path(local_rel: str) -> str:
    return ENTRY_MAP.get(local_rel, local_rel)


def is_direct_raw_asset(rel: str, direct_asset_refs: set[str]) -> bool:
    if rel not in direct_asset_refs:
        return False
    suffix = Path(rel).suffix.lower()
    return suffix in {".pdf", ".epub", ".mobi"}


def always_copy_asset(rel: str) -> bool:
    if rel == "b132-source-preview-fix.js":
        return True
    prefixes = (
        "files/source_slices/",
        "files/open_enrichment/",
        "files/open_enrichment_fragments/",
        "files/ielts18_sample_safe/",
        "rendered/",
    )
    return rel.startswith(prefixes)


def asset_release_name(rel: str) -> str:
    name = Path(rel).name
    digest = hashlib.sha1(rel.encode("utf-8")).hexdigest()[:8]
    stem = Path(name).stem
    suffix = Path(name).suffix
    return f"{stem}-{digest}{suffix}"


def release_url(rel: str) -> str:
    return f"{RELEASE_BASE}/{RELEASE_TAG}/{quote(asset_release_name(rel))}"


def rel_url(from_public_html: str, to_public_rel: str, query: str = "", fragment: str = "") -> str:
    from_dir = posixpath.dirname(from_public_html)
    if not from_dir:
        base = to_public_rel
    else:
        base = posixpath.relpath(to_public_rel, from_dir)
    return with_suffix_url(base, query, fragment)


def refs_in_html(path: Path) -> list[tuple[str, str]]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html5lib")
    refs: list[tuple[str, str]] = []
    for tag in soup.find_all(True):
        for attr in ("href", "src"):
            if tag.get(attr):
                refs.append((attr, tag.get(attr)))
    return refs


def gather_html(local_viewer: Path, max_depth: int) -> tuple[set[str], set[str], set[str]]:
    html_to_copy = set(ENTRY_SOURCES)
    direct_asset_refs: set[str] = set()
    all_refs: set[str] = set()
    queue: list[tuple[str, int]] = [(rel, 0) for rel in ENTRY_SOURCES]

    while queue:
        html_rel, depth = queue.pop(0)
        html_path = local_viewer / html_rel
        if not html_path.exists():
            continue
        for _, ref in refs_in_html(html_path):
            parts = parse_ref(ref)
            if not parts:
                continue
            resolved = resolve_local_ref(local_viewer, html_rel, parts.path)
            if not resolved:
                continue
            if resolved == "index.html":
                all_refs.add(resolved)
                continue
            all_refs.add(resolved)
            local_path = local_viewer / resolved
            if depth == 0 and local_path.exists() and not resolved.endswith(".html"):
                direct_asset_refs.add(resolved)
            if (
                local_path.exists()
                and resolved.endswith(".html")
                and resolved not in html_to_copy
                and (
                    depth < max_depth
                    or resolved.startswith("files/open_enrichment_fragments/")
                    or resolved in ALWAYS_INCLUDE_HTML
                )
            ):
                html_to_copy.add(resolved)
                queue.append((resolved, depth + 1))
    return html_to_copy, direct_asset_refs, all_refs


def choose_assets(local_viewer: Path, html_to_copy: set[str], direct_asset_refs: set[str]) -> tuple[set[str], set[str]]:
    assets_to_copy: set[str] = set()
    assets_to_release: set[str] = set()

    for html_rel in sorted(html_to_copy):
        html_path = local_viewer / html_rel
        if not html_path.exists():
            continue
        for _, ref in refs_in_html(html_path):
            parts = parse_ref(ref)
            if not parts:
                continue
            resolved = resolve_local_ref(local_viewer, html_rel, parts.path)
            if not resolved:
                continue
            local_path = local_viewer / resolved
            if not local_path.exists() or local_path.is_dir() or resolved.endswith(".html"):
                continue
            size_mb = local_path.stat().st_size / 1024 / 1024
            if always_copy_asset(resolved):
                assets_to_copy.add(resolved)
            elif Path(resolved).suffix.lower() in {".pdf", ".epub", ".mobi", ".doc", ".docx", ".ppt", ".pptx"}:
                assets_to_release.add(resolved)
            elif size_mb > MAX_PAGES_FILE_MB:
                assets_to_release.add(resolved)
    return assets_to_copy, assets_to_release


def copy_file(local_viewer: Path, deploy: Path, rel: str) -> None:
    src = local_viewer / rel
    dst = deploy / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        if dst.exists() and dst.stat().st_size == src.stat().st_size:
            return
    except OSError:
        pass
    if src.is_symlink():
        subprocess.run(["/usr/bin/rsync", "-aL", os.fspath(src), os.fspath(dst)], check=True)
    else:
        shutil.copy2(src, dst)


def make_unavailable_page(deploy: Path) -> None:
    target = deploy / "files" / "_source_asset_not_in_packet.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        """<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>B132 source asset route</title>
  <style>
    body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;margin:0;padding:32px;background:#f7f5ef;color:#1f2933;line-height:1.7}
    main{max-width:760px;margin:auto;background:white;border:1px solid #ddd6c8;border-radius:14px;padding:28px;box-shadow:0 14px 40px rgba(31,41,51,.08)}
    code{background:#f2efe7;padding:2px 6px;border-radius:6px;word-break:break-all}
    .badge{display:inline-block;border:1px solid #c9b27a;background:#fff8df;color:#6b4e16;border-radius:999px;padding:4px 10px;font-size:13px}
  </style>
</head>
<body><main>
  <span class="badge">完整原書檔案未放入這個學生包</span>
  <h1>請回到上一頁使用切頁 PDF</h1>
  <p>這個按鈕原本指向完整原書或大型 raw asset。學生公開包優先放入可直接開啟的切頁 PDF、片段文本、練習頁與互動頁；若需要完整原書，請使用老師端 B132 viewer 或同頁的已切頁來源。</p>
  <p>資源路線：<code id="asset"></code></p>
  <p><button onclick="history.back()">回上一頁</button></p>
  <script>
    const params = new URLSearchParams(location.search);
    document.getElementById('asset').textContent = params.get('asset') || '(not specified)';
  </script>
</main></body></html>
""",
        encoding="utf-8",
    )


def rewrite_html(
    local_viewer: Path,
    deploy: Path,
    html_rel: str,
    html_to_copy: set[str],
    assets_to_copy: set[str],
    assets_to_release: set[str],
) -> list[dict[str, str]]:
    src = local_viewer / html_rel
    public_rel = public_html_path(html_rel)
    dst = deploy / public_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    soup = BeautifulSoup(src.read_text(encoding="utf-8", errors="ignore"), "html5lib")
    rewrites: list[dict[str, str]] = []

    for tag in soup.find_all(True):
        for attr in ("href", "src"):
            value = tag.get(attr)
            parts = parse_ref(value)
            if not parts:
                if value == "index.html":
                    tag[attr] = "./"
                continue
            resolved = resolve_local_ref(local_viewer, html_rel, parts.path)
            if not resolved:
                continue
            local_path = local_viewer / resolved
            if resolved == "index.html":
                tag[attr] = rel_url(public_rel, "index.html", parts.query, parts.fragment)
            elif local_path.exists() and resolved.endswith(".html") and resolved in html_to_copy:
                tag[attr] = rel_url(public_rel, public_html_path(resolved), parts.query, parts.fragment)
            elif local_path.exists() and resolved in assets_to_copy:
                tag[attr] = rel_url(public_rel, resolved, parts.query, parts.fragment)
            elif local_path.exists() and resolved in assets_to_release:
                tag[attr] = release_url(resolved)
                rewrites.append(
                    {
                        "html": html_rel,
                        "from": value,
                        "to": tag[attr],
                        "reason": "github_release_asset",
                    }
                )
            elif local_path.exists() and not resolved.endswith(".html"):
                fallback = "files/_source_asset_not_in_packet.html"
                query = f"asset={quote(resolved)}"
                tag[attr] = rel_url(public_rel, fallback, query, "")
                rewrites.append(
                    {
                        "html": html_rel,
                        "from": value,
                        "to": tag[attr],
                        "reason": "not_in_student_packet",
                    }
                )
            elif resolved.endswith(".html") and resolved not in html_to_copy:
                fallback = "files/_source_asset_not_in_packet.html"
                query = f"asset={quote(resolved)}"
                tag[attr] = rel_url(public_rel, fallback, query, "")
                rewrites.append(
                    {
                        "html": html_rel,
                        "from": value,
                        "to": tag[attr],
                        "reason": "html_not_in_student_packet",
                    }
                )

    dst.write_text(str(soup), encoding="utf-8")
    return rewrites


def write_report(
    deploy: Path,
    html_to_copy: set[str],
    assets_to_copy: set[str],
    assets_to_release: set[str],
    rewrites: list[dict[str, str]],
) -> None:
    report = deploy / "ETHAN_PUBLIC_PACKET_REPORT.md"
    copied_size = sum((deploy / rel).stat().st_size for rel in assets_to_copy if (deploy / rel).exists())
    report.write_text(
        "\n".join(
            [
                "# Ethan GEPT Public Packet Report",
                "",
                "This packet exports the local B132 teacher-view pages as student-clickable public pages.",
                "",
                f"- HTML pages exported: {len(html_to_copy)}",
                f"- Assets copied into GitHub Pages: {len(assets_to_copy)}",
                f"- Copied asset size: {copied_size / 1024 / 1024:.1f} MB",
                f"- Large assets routed through GitHub Release: {len(assets_to_release)}",
                f"- Non-exported route fallbacks: {sum(1 for r in rewrites if r['reason'].endswith('packet'))}",
                "",
                "## Entry Pages",
                "",
                *[f"- `{public}` from `{local}`" for local, public in ENTRY_MAP.items()],
                "",
                "## Release Assets Needed",
                "",
                *[f"- `{rel}` -> `{release_url(rel)}`" for rel in sorted(assets_to_release)],
                "",
                "## Rewrites",
                "",
                *[
                    f"- `{row['html']}`: `{row['from']}` -> `{row['to']}` ({row['reason']})"
                    for row in rewrites[:300]
                ],
                "",
            ]
        ),
        encoding="utf-8",
    )

    csv_path = deploy / "ETHAN_PUBLIC_PACKET_LINK_REWRITES.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["html", "from", "to", "reason"])
        writer.writeheader()
        writer.writerows(rewrites)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-viewer", required=True)
    parser.add_argument("--deploy", required=True)
    parser.add_argument("--html-depth", type=int, default=2)
    args = parser.parse_args()

    local_viewer = Path(args.local_viewer).expanduser().resolve()
    deploy = Path(args.deploy).expanduser().resolve()

    html_to_copy, direct_asset_refs, _ = gather_html(local_viewer, args.html_depth)
    assets_to_copy, assets_to_release = choose_assets(local_viewer, html_to_copy, direct_asset_refs)

    make_unavailable_page(deploy)
    for rel in sorted(assets_to_copy):
        copy_file(local_viewer, deploy, rel)

    rewrites: list[dict[str, str]] = []
    for html_rel in sorted(html_to_copy):
        rewrites.extend(
            rewrite_html(local_viewer, deploy, html_rel, html_to_copy, assets_to_copy, assets_to_release)
        )

    write_report(deploy, html_to_copy, assets_to_copy, assets_to_release, rewrites)
    print(f"exported_html={len(html_to_copy)}")
    print(f"copied_assets={len(assets_to_copy)}")
    print(f"release_assets={len(assets_to_release)}")
    print(f"rewrites={len(rewrites)}")


if __name__ == "__main__":
    main()
