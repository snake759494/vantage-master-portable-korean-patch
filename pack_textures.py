"""Put patched textures into the pack archives the game actually reads.

``data/system/*.itp`` are loose copies; at runtime the loader pulls the same
files out of ``data/pack/*.dat`` -- exactly the trap ``pspfont.dat`` set
earlier, where the loose font was ignored in favour of the copy inside
``init0.dat``.  Every texture entry in these packs is stored raw (its record
declares an uncompressed size of 0), so a replacement of identical length can
be spliced straight in and the pack keeps its size.
"""

from __future__ import annotations

import pycdlib

from patch_packed_pspfont import PACK_HEADER_SIZE, PACK_RECORD_SIZE, parse_pack_record, u32

PACK_DIR = "/PSP_GAME/USRDIR/data/pack"


def pack_records(pack: bytes) -> list[tuple[str, int, int, int, int]]:
    count = u32(pack, 0)
    if not 0 < count < 10000:
        raise ValueError(f"implausible pack record count: {count}")
    if PACK_HEADER_SIZE + count * PACK_RECORD_SIZE > len(pack):
        raise ValueError("pack record table runs past the end of the file")
    return [parse_pack_record(pack, index) for index in range(count)]


def find_packs(iso_path, wanted: set[str]) -> dict[str, list[tuple[str, int]]]:
    """Map each wanted member name to the (pack file, record index) holding it."""
    located: dict[str, list[tuple[str, int]]] = {}
    with open(iso_path, "rb") as handle:
        iso = pycdlib.PyCdlib()
        iso.open_fp(handle)
        try:
            children = [
                child.file_identifier().decode().split(";")[0]
                for child in iso.list_children(iso_path=PACK_DIR)
                if not (child.is_dot() or child.is_dotdot())
            ]
            for name in sorted(children):
                with iso.open_file_from_iso(iso_path=f"{PACK_DIR}/{name}") as member:
                    head = member.read(PACK_HEADER_SIZE)
                count = u32(head, 0)
                if not 0 < count < 10000:
                    continue
                with iso.open_file_from_iso(iso_path=f"{PACK_DIR}/{name}") as member:
                    table = member.read(PACK_HEADER_SIZE + count * PACK_RECORD_SIZE)
                for index in range(count):
                    member_name = parse_pack_record(table, index)[0]
                    if member_name in wanted:
                        located.setdefault(member_name, []).append((name, index))
        finally:
            iso.close()
    return located


def splice(pack: bytes, index: int, replacement: bytes) -> bytes:
    """Overwrite one raw pack member; the replacement must be the same size."""
    name, data_offset, stored_size, uncompressed_size, _flags = parse_pack_record(pack, index)
    if uncompressed_size:
        raise ValueError(f"{name} is compressed in this pack; splicing is not valid")
    if len(replacement) != stored_size:
        raise ValueError(
            f"{name}: replacement is {len(replacement)} bytes, the record holds {stored_size}"
        )
    if data_offset + stored_size > len(pack):
        raise ValueError(f"{name}: record runs past the end of the pack")
    return pack[:data_offset] + replacement + pack[data_offset + stored_size :]
