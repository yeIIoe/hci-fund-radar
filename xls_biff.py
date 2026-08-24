"""Leitor pequeno de XLS/BIFF8 para tabelas historicas oficiais.

O projeto evita instalar dependencias. Este modulo implementa somente o
subconjunto necessario para ler planilhas BIFF8 simples: workbook OLE,
BoundSheet, SST e celulas numericas/textuais. Nao pretende substituir um
leitor Excel geral.
"""
from __future__ import annotations

import struct
from pathlib import Path


FREESECT = 0xFFFFFFFF
ENDOFCHAIN = 0xFFFFFFFE


class XlsError(RuntimeError):
    pass


def _u16(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def _u32(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def _decode_rk(raw: int) -> float:
    divided = bool(raw & 0x01)
    if raw & 0x02:
        signed = struct.unpack("<i", struct.pack("<I", raw))[0]
        value = float(signed >> 2)
    else:
        value = struct.unpack("<d", struct.pack("<II", 0, raw & 0xFFFFFFFC))[0]
    return value / 100.0 if divided else value


class _CompoundFile:
    def __init__(self, payload: bytes):
        if payload[:8] != bytes.fromhex("D0CF11E0A1B11AE1"):
            raise XlsError("arquivo nao e um XLS OLE/BIFF")
        self.payload = payload
        self.sector_size = 1 << _u16(payload, 0x1E)
        self.mini_sector_size = 1 << _u16(payload, 0x20)
        self.first_dir_sector = _u32(payload, 0x30)
        self.mini_cutoff = _u32(payload, 0x38)
        self.first_minifat_sector = _u32(payload, 0x3C)
        self.minifat_sector_count = _u32(payload, 0x40)
        first_difat = _u32(payload, 0x44)
        difat_count = _u32(payload, 0x48)

        difat = [value for value in struct.unpack_from("<109I", payload, 0x4C) if value != FREESECT]
        sector = first_difat
        for _ in range(difat_count):
            if sector in (FREESECT, ENDOFCHAIN):
                break
            block = self._sector(sector)
            values = struct.unpack(f"<{self.sector_size // 4}I", block)
            difat.extend(value for value in values[:-1] if value != FREESECT)
            sector = values[-1]

        fat: list[int] = []
        for fat_sector in difat:
            fat.extend(struct.unpack(f"<{self.sector_size // 4}I", self._sector(fat_sector)))
        self.fat = fat

        directory = self._read_chain(self.first_dir_sector)
        self.entries: dict[str, tuple[int, int, int]] = {}
        self.root: tuple[int, int, int] | None = None
        for offset in range(0, len(directory), 128):
            entry = directory[offset:offset + 128]
            if len(entry) < 128:
                continue
            name_length = _u16(entry, 64)
            entry_type = entry[66]
            if name_length < 2 or entry_type == 0:
                continue
            name = entry[:name_length - 2].decode("utf-16le", errors="replace")
            start = _u32(entry, 116)
            size = struct.unpack_from("<Q", entry, 120)[0]
            record = (entry_type, start, size)
            self.entries[name] = record
            if entry_type == 5:
                self.root = record

        self.minifat: list[int] = []
        if self.minifat_sector_count and self.first_minifat_sector not in (FREESECT, ENDOFCHAIN):
            raw = self._read_chain(self.first_minifat_sector)
            self.minifat = list(struct.unpack(f"<{len(raw) // 4}I", raw[:len(raw) // 4 * 4]))
        self.mini_stream = b""
        if self.root is not None:
            _, start, size = self.root
            self.mini_stream = self._read_chain(start)[:size]

    def _sector(self, index: int) -> bytes:
        start = 512 + index * self.sector_size
        return self.payload[start:start + self.sector_size]

    def _read_chain(self, start: int) -> bytes:
        output = bytearray()
        sector = start
        seen: set[int] = set()
        while sector not in (FREESECT, ENDOFCHAIN):
            if sector in seen or sector >= len(self.fat):
                raise XlsError("cadeia OLE corrompida")
            seen.add(sector)
            output.extend(self._sector(sector))
            sector = self.fat[sector]
        return bytes(output)

    def _read_mini_chain(self, start: int) -> bytes:
        output = bytearray()
        sector = start
        seen: set[int] = set()
        while sector not in (FREESECT, ENDOFCHAIN):
            if sector in seen or sector >= len(self.minifat):
                raise XlsError("mini cadeia OLE corrompida")
            seen.add(sector)
            offset = sector * self.mini_sector_size
            output.extend(self.mini_stream[offset:offset + self.mini_sector_size])
            sector = self.minifat[sector]
        return bytes(output)

    def stream(self, *names: str) -> bytes:
        for name in names:
            if name not in self.entries:
                continue
            _, start, size = self.entries[name]
            raw = self._read_mini_chain(start) if size < self.mini_cutoff else self._read_chain(start)
            return raw[:size]
        raise XlsError(f"stream ausente: {', '.join(names)}")


def _records(stream: bytes, start: int = 0):
    offset = start
    while offset + 4 <= len(stream):
        code, size = struct.unpack_from("<HH", stream, offset)
        payload_start = offset + 4
        payload_end = payload_start + size
        if payload_end > len(stream):
            break
        yield offset, code, stream[payload_start:payload_end]
        offset = payload_end


class _Segments:
    def __init__(self, chunks: list[bytes]):
        self.chunks = chunks
        self.chunk = 0
        self.offset = 0

    def _advance(self) -> None:
        while self.chunk < len(self.chunks) and self.offset >= len(self.chunks[self.chunk]):
            self.chunk += 1
            self.offset = 0

    def read(self, size: int) -> bytes:
        output = bytearray()
        while size:
            self._advance()
            if self.chunk >= len(self.chunks):
                raise XlsError("SST truncada")
            available = len(self.chunks[self.chunk]) - self.offset
            take = min(size, available)
            output.extend(self.chunks[self.chunk][self.offset:self.offset + take])
            self.offset += take
            size -= take
        return bytes(output)

    def read_chars(self, count: int, wide: bool) -> str:
        pieces: list[str] = []
        remaining = count
        while remaining:
            self._advance()
            if self.chunk >= len(self.chunks):
                raise XlsError("texto SST truncado")
            width = 2 if wide else 1
            available_chars = (len(self.chunks[self.chunk]) - self.offset) // width
            if available_chars == 0:
                self.chunk += 1
                self.offset = 0
                if self.chunk >= len(self.chunks):
                    raise XlsError("continuacao SST ausente")
                option = self.chunks[self.chunk][0]
                self.offset = 1
                wide = bool(option & 0x01)
                continue
            take = min(remaining, available_chars)
            raw = self.read(take * width)
            pieces.append(raw.decode("utf-16le" if wide else "latin1", errors="replace"))
            remaining -= take
            if remaining and self.offset >= len(self.chunks[self.chunk]):
                self.chunk += 1
                self.offset = 0
                if self.chunk >= len(self.chunks):
                    raise XlsError("continuacao SST ausente")
                option = self.chunks[self.chunk][0]
                self.offset = 1
                wide = bool(option & 0x01)
        return "".join(pieces)


def _parse_sst(chunks: list[bytes]) -> list[str]:
    reader = _Segments(chunks)
    reader.read(4)  # total de ocorrencias
    unique = _u32(reader.read(4))
    strings: list[str] = []
    for _ in range(unique):
        count = _u16(reader.read(2))
        flags = reader.read(1)[0]
        rich_runs = _u16(reader.read(2)) if flags & 0x08 else 0
        extension_size = _u32(reader.read(4)) if flags & 0x04 else 0
        strings.append(reader.read_chars(count, bool(flags & 0x01)))
        if rich_runs:
            reader.read(4 * rich_runs)
        if extension_size:
            reader.read(extension_size)
    return strings


def _short_unicode(payload: bytes, offset: int) -> str:
    count = payload[offset]
    flags = payload[offset + 1]
    width = 2 if flags & 0x01 else 1
    raw = payload[offset + 2:offset + 2 + count * width]
    return raw.decode("utf-16le" if width == 2 else "latin1", errors="replace")


def workbook_sheets(path: Path) -> tuple[bytes, dict[str, int], list[str], int]:
    stream = _CompoundFile(path.read_bytes()).stream("Workbook", "Book")
    sheets: dict[str, int] = {}
    sst: list[str] = []
    date_mode = 0
    records = list(_records(stream))
    index = 0
    while index < len(records):
        _, code, payload = records[index]
        if code == 0x0085 and len(payload) >= 8:
            sheets[_short_unicode(payload, 6)] = _u32(payload, 0)
        elif code == 0x0022 and len(payload) >= 2:
            date_mode = _u16(payload, 0)
        elif code == 0x00FC:
            chunks = [payload]
            cursor = index + 1
            while cursor < len(records) and records[cursor][1] == 0x003C:
                chunks.append(records[cursor][2])
                cursor += 1
            sst = _parse_sst(chunks)
            index = cursor - 1
        index += 1
    return stream, sheets, sst, date_mode


def read_sheet(path: Path, preferred: tuple[str, ...] = ("Data",)) -> tuple[str, list[list[object]], int]:
    stream, sheets, sst, date_mode = workbook_sheets(path)
    if not sheets:
        raise XlsError("nenhuma planilha encontrada")
    sheet_name = next((name for name in preferred if name in sheets), next(iter(sheets)))
    cells: dict[tuple[int, int], object] = {}
    max_row = max_col = 0
    for _, code, payload in _records(stream, sheets[sheet_name]):
        if code == 0x000A:
            break
        if code == 0x0203 and len(payload) >= 14:  # NUMBER
            row, col = _u16(payload, 0), _u16(payload, 2)
            value: object = struct.unpack_from("<d", payload, 6)[0]
            cells[(row, col)] = value
        elif code == 0x027E and len(payload) >= 10:  # RK
            row, col = _u16(payload, 0), _u16(payload, 2)
            cells[(row, col)] = _decode_rk(_u32(payload, 6))
        elif code == 0x00BD and len(payload) >= 12:  # MULRK
            row, first_col, last_col = _u16(payload, 0), _u16(payload, 2), _u16(payload, len(payload) - 2)
            for col in range(first_col, last_col + 1):
                item = 4 + (col - first_col) * 6
                cells[(row, col)] = _decode_rk(_u32(payload, item + 2))
        elif code == 0x00FD and len(payload) >= 10:  # LABELSST
            row, col, string_index = _u16(payload, 0), _u16(payload, 2), _u32(payload, 6)
            cells[(row, col)] = sst[string_index] if string_index < len(sst) else ""
        elif code == 0x0204 and len(payload) >= 9:  # LABEL
            row, col, count = _u16(payload, 0), _u16(payload, 2), _u16(payload, 6)
            flags = payload[8]
            width = 2 if flags & 0x01 else 1
            raw = payload[9:9 + count * width]
            cells[(row, col)] = raw.decode("utf-16le" if width == 2 else "latin1", errors="replace")
        elif code == 0x0006 and len(payload) >= 14:  # FORMULA com resultado numerico
            row, col = _u16(payload, 0), _u16(payload, 2)
            result = payload[6:14]
            if result[6:8] != b"\xff\xff":
                cells[(row, col)] = struct.unpack("<d", result)[0]
        else:
            continue
        max_row = max(max_row, row)
        max_col = max(max_col, col)
    rows = [[cells.get((row, col)) for col in range(max_col + 1)] for row in range(max_row + 1)]
    return sheet_name, rows, date_mode

