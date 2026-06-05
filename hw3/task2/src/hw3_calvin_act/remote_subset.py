from __future__ import annotations

import binascii
import io
import json
import os
import shutil
import struct
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Iterator, Sequence

import numpy as np
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ARCHIVES = {
    "ABC": {
        "task_name": "task_ABC_D",
        "split": "training",
        "url": "http://calvin.cs.uni-freiburg.de/dataset/task_ABC_D.zip",
        "scene_ranges": {
            "B": (0, 598909),
            "C": (598910, 1191338),
            "A": (1191339, 1795044),
        },
    },
    "D": {
        "task_name": "task_D_D",
        "split": "validation",
        "url": "http://calvin.cs.uni-freiburg.de/dataset/task_D_D.zip",
        "scene_ranges": {},
    },
}


@dataclass(frozen=True)
class ArchiveMetadata:
    url: str
    content_length: int
    directory_offset: int
    directory_size: int
    entries: int


@dataclass(frozen=True)
class RemoteEntry:
    filename: str
    header_offset: int
    compress_type: int
    compress_size: int
    file_size: int
    crc: int
    flag_bits: int


class HttpRangeReader(io.RawIOBase):
    def __init__(self, url: str, session: requests.Session | None = None) -> None:
        self.url = url
        self.session = session or make_session()
        response = self.session.head(url, allow_redirects=True, timeout=60)
        response.raise_for_status()
        self.length = int(response.headers["Content-Length"])
        self.position = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            self.position = offset
        elif whence == io.SEEK_CUR:
            self.position += offset
        elif whence == io.SEEK_END:
            self.position = self.length + offset
        else:
            raise ValueError(f"Unsupported whence: {whence}")
        return self.position

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            size = self.length - self.position
        if size == 0 or self.position >= self.length:
            return b""
        data = request_range(self.session, self.url, self.position, self.position + size - 1)
        self.position += len(data)
        return data


def make_session() -> requests.Session:
    retries = Retry(
        total=5,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
    )
    session = requests.Session()
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def request_range(session: requests.Session, url: str, start: int, end: int) -> bytes:
    response = session.get(url, headers={"Range": f"bytes={start}-{end}"}, timeout=180)
    response.raise_for_status()
    if response.status_code != 206:
        raise RuntimeError(f"Server did not honor HTTP Range for {url}: {response.status_code}")
    return response.content


def fetch_archive_metadata(url: str) -> ArchiveMetadata:
    reader = HttpRangeReader(url)
    end_record = zipfile._EndRecData(reader)
    if not end_record:
        raise zipfile.BadZipFile(f"Could not read ZIP end record: {url}")
    return ArchiveMetadata(
        url=url,
        content_length=reader.length,
        directory_offset=int(end_record[zipfile._ECD_OFFSET]),
        directory_size=int(end_record[zipfile._ECD_SIZE]),
        entries=int(end_record[zipfile._ECD_ENTRIES_TOTAL]),
    )


def ensure_central_directory(metadata: ArchiveMetadata, cache_root: str | Path, task_name: str) -> Path:
    cache_root = Path(cache_root)
    cache_root.mkdir(parents=True, exist_ok=True)
    directory_path = cache_root / f"{task_name}.central-directory.bin"
    metadata_path = cache_root / f"{task_name}.central-directory.json"
    expected_metadata = asdict(metadata)
    if directory_path.exists() and metadata_path.exists():
        cached_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if cached_metadata == expected_metadata and directory_path.stat().st_size == metadata.directory_size:
            return directory_path

    session = make_session()
    end = metadata.directory_offset + metadata.directory_size - 1
    response = session.get(
        metadata.url,
        headers={"Range": f"bytes={metadata.directory_offset}-{end}"},
        stream=True,
        timeout=180,
    )
    response.raise_for_status()
    if response.status_code != 206:
        raise RuntimeError(f"Server did not honor HTTP Range for {metadata.url}: {response.status_code}")
    temporary_path = directory_path.with_suffix(".tmp")
    with temporary_path.open("wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                file.write(chunk)
    if temporary_path.stat().st_size != metadata.directory_size:
        raise IOError(f"Truncated central directory: {temporary_path}")
    temporary_path.replace(directory_path)
    metadata_path.write_text(json.dumps(expected_metadata, indent=2), encoding="utf-8")
    return directory_path


def iter_central_directory(directory_path: str | Path) -> Iterator[RemoteEntry]:
    with Path(directory_path).open("rb") as file:
        while True:
            record = file.read(zipfile.sizeCentralDir)
            if not record:
                return
            if len(record) != zipfile.sizeCentralDir:
                raise zipfile.BadZipFile(f"Truncated central directory: {directory_path}")
            central = struct.unpack(zipfile.structCentralDir, record)
            if central[zipfile._CD_SIGNATURE] != zipfile.stringCentralDir:
                raise zipfile.BadZipFile(f"Bad central directory signature: {directory_path}")
            filename_bytes = file.read(central[zipfile._CD_FILENAME_LENGTH])
            filename_crc = binascii.crc32(filename_bytes)
            if central[zipfile._CD_FLAG_BITS] & zipfile._MASK_UTF_FILENAME:
                filename = filename_bytes.decode("utf-8")
            else:
                filename = filename_bytes.decode("cp437")
            info = zipfile.ZipInfo(filename)
            info.extra = file.read(central[zipfile._CD_EXTRA_FIELD_LENGTH])
            info.comment = file.read(central[zipfile._CD_COMMENT_LENGTH])
            info.header_offset = central[zipfile._CD_LOCAL_HEADER_OFFSET]
            (
                info.create_version,
                info.create_system,
                info.extract_version,
                info.reserved,
                info.flag_bits,
                info.compress_type,
                _,
                _,
                info.CRC,
                info.compress_size,
                info.file_size,
            ) = central[1:12]
            info._decodeExtra(filename_crc)
            yield RemoteEntry(
                filename=info.filename,
                header_offset=int(info.header_offset),
                compress_type=int(info.compress_type),
                compress_size=int(info.compress_size),
                file_size=int(info.file_size),
                crc=int(info.CRC),
                flag_bits=int(info.flag_bits),
            )


def frame_prefix(task_name: str, split: str) -> str:
    return f"{task_name}/{split}/episode_"


def parse_frame_filename(filename: str, task_name: str, split: str) -> int | None:
    prefix = frame_prefix(task_name, split)
    if not filename.startswith(prefix) or not filename.endswith(".npz"):
        return None
    value = filename[len(prefix) : -4]
    return int(value) if value.isdigit() else None


def available_frame_indices(directory_path: str | Path, task_name: str, split: str) -> list[int]:
    indices = []
    for entry in iter_central_directory(directory_path):
        frame_index = parse_frame_filename(entry.filename, task_name, split)
        if frame_index is not None:
            indices.append(frame_index)
    return sorted(indices)


def choose_window_frames(
    available_indices: Sequence[int],
    ranges: Sequence[tuple[int, int]],
    windows_per_range: int,
    window_size: int,
) -> list[int]:
    if windows_per_range <= 0 or window_size <= 0:
        raise ValueError("windows_per_range and window_size must both be positive.")
    available = set(available_indices)
    selected = set()
    for start, end in ranges:
        in_range = sorted(index for index in available if start <= index <= end)
        if len(in_range) < window_size:
            raise ValueError(f"Window size {window_size} exceeds range {start}..{end}")
        valid_starts = []
        streak = 0
        previous = None
        for index in in_range:
            streak = streak + 1 if previous is not None and index == previous + 1 else 1
            if streak >= window_size:
                valid_starts.append(index - window_size + 1)
            previous = index
        if not valid_starts:
            raise ValueError(f"No consecutive {window_size}-frame windows exist in range {start}..{end}")
        positions = np.linspace(0, len(valid_starts) - 1, num=windows_per_range, dtype=np.int64)
        for position in positions:
            frame_window = range(valid_starts[int(position)], valid_starts[int(position)] + window_size)
            selected.update(frame_window)
    return sorted(selected)


def select_entries(
    directory_path: str | Path,
    task_name: str,
    split: str,
    selected_frames: Iterable[int],
) -> list[RemoteEntry]:
    expected = {f"{frame_prefix(task_name, split)}{frame_index:07d}.npz" for frame_index in selected_frames}
    entries = [entry for entry in iter_central_directory(directory_path) if entry.filename in expected]
    found = {entry.filename for entry in entries}
    missing = sorted(expected - found)
    if missing:
        raise FileNotFoundError(f"Remote ZIP index is missing {len(missing)} selected entries, first={missing[0]}")
    return entries


def safe_output_path(output_root: str | Path, filename: str) -> Path:
    relative = PurePosixPath(filename)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe ZIP member path: {filename}")
    return Path(output_root).joinpath(*relative.parts)


def extract_entry(session: requests.Session, url: str, entry: RemoteEntry, output_root: str | Path) -> Path:
    destination = safe_output_path(output_root, entry.filename)
    if destination.exists() and destination.stat().st_size == entry.file_size:
        return destination
    if entry.flag_bits & 0x1:
        raise NotImplementedError(f"Encrypted ZIP member is unsupported: {entry.filename}")

    header = request_range(
        session,
        url,
        entry.header_offset,
        entry.header_offset + zipfile.sizeFileHeader - 1,
    )
    values = struct.unpack(zipfile.structFileHeader, header)
    if values[zipfile._FH_SIGNATURE] != zipfile.stringFileHeader:
        raise zipfile.BadZipFile(f"Bad local header for {entry.filename}")
    data_offset = (
        entry.header_offset
        + zipfile.sizeFileHeader
        + values[zipfile._FH_FILENAME_LENGTH]
        + values[zipfile._FH_EXTRA_FIELD_LENGTH]
    )
    compressed = request_range(session, url, data_offset, data_offset + entry.compress_size - 1)
    if entry.compress_type == zipfile.ZIP_STORED:
        payload = compressed
    else:
        decompressor = zipfile._get_decompressor(entry.compress_type)
        payload = decompressor.decompress(compressed)
        payload += decompressor.flush()
    if len(payload) != entry.file_size:
        raise IOError(f"Unexpected extracted size for {entry.filename}")
    if binascii.crc32(payload) & 0xFFFFFFFF != entry.crc:
        raise IOError(f"CRC mismatch for {entry.filename}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination.with_suffix(destination.suffix + ".tmp")
    temporary_path.write_bytes(payload)
    temporary_path.replace(destination)
    return destination


def extract_entries(
    url: str,
    entries: Sequence[RemoteEntry],
    output_root: str | Path,
    workers: int,
) -> list[Path]:
    def worker(entry: RemoteEntry) -> Path:
        with make_session() as session:
            return extract_entry(session, url, entry, output_root)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(worker, entries))


def install_abc_scene_info(output_root: str | Path) -> Path:
    url = "http://calvin.cs.uni-freiburg.de/scene_info_fix/task_ABC_D_scene_info.zip"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        member = next(name for name in archive.namelist() if name.endswith("scene_info.npy"))
        destination = Path(output_root) / "task_ABC_D" / "training" / "scene_info.npy"
        destination.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(member) as source, destination.open("wb") as target:
            shutil.copyfileobj(source, target)
    return destination


def download_archive_subset(
    archive: str,
    output_root: str | Path,
    cache_root: str | Path,
    windows_per_env: int,
    window_size: int,
    workers: int,
    index_only: bool = False,
) -> dict:
    spec = ARCHIVES[archive]
    task_name = spec["task_name"]
    split = spec["split"]
    metadata = fetch_archive_metadata(spec["url"])
    directory_path = ensure_central_directory(metadata, cache_root, task_name)
    available = available_frame_indices(directory_path, task_name, split)
    if not available:
        raise FileNotFoundError(f"No frames found for {task_name}/{split}")

    if archive == "ABC":
        ranges = [spec["scene_ranges"][environment] for environment in "BCA"]
    else:
        ranges = [(available[0], available[-1])]
    selected_frames = choose_window_frames(available, ranges, windows_per_env, window_size)
    entries = select_entries(directory_path, task_name, split, selected_frames)
    expected_download_bytes = sum(entry.compress_size for entry in entries)
    extracted = []
    if not index_only:
        extracted = extract_entries(spec["url"], entries, output_root, workers)
        if archive == "ABC":
            install_abc_scene_info(output_root)

    summary = {
        "archive": archive,
        "source_url": spec["url"],
        "task_name": task_name,
        "split": split,
        "remote_archive_bytes": metadata.content_length,
        "cached_directory_bytes": metadata.directory_size,
        "selected_frames": len(selected_frames),
        "expected_download_bytes": expected_download_bytes,
        "index_only": index_only,
        "output_root": str(Path(output_root).resolve()),
        "extracted_files": len(extracted),
    }
    manifest_path = Path(output_root) / f"{task_name}_subset_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def default_cache_root() -> Path:
    return Path(os.getenv("HF_HOME", "data/cache")) / "calvin-remote-index"


def default_output_root() -> Path:
    return Path(os.getenv("HW3_TASK2_DATA_ROOT", "data/calvin-subset"))
