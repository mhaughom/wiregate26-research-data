#!/usr/bin/env python3
"""Minimal parser for the protobuf wire format used by Immersiv ATS segments.

This parser intentionally extracts only entity identifiers and positions.  It
does not depend on a recovered proprietary schema and does not distribute any
source segment.
"""

from __future__ import annotations

import struct
from pathlib import Path


def read_varint(buffer: bytes, index: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if index >= len(buffer):
            raise ValueError("truncated varint")
        byte = buffer[index]
        index += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, index
        shift += 7
        if shift > 70:
            raise ValueError("invalid varint")


def fields(buffer: bytes):
    index = 0
    while index < len(buffer):
        tag, index = read_varint(buffer, index)
        field_number, wire_type = tag >> 3, tag & 7
        if wire_type == 0:
            value, index = read_varint(buffer, index)
        elif wire_type == 1:
            value = buffer[index : index + 8]
            index += 8
        elif wire_type == 2:
            length, index = read_varint(buffer, index)
            value = buffer[index : index + length]
            index += length
        elif wire_type == 5:
            value = buffer[index : index + 4]
            index += 4
        else:
            raise ValueError(f"unsupported protobuf wire type {wire_type}")
        yield field_number, wire_type, value


def parse_position(buffer: bytes) -> tuple[float | None, float | None, float | None]:
    coordinates: list[float | None] = [None, None, None]
    for field_number, wire_type, value in fields(buffer):
        if wire_type == 5 and 1 <= field_number <= 3:
            coordinates[field_number - 1] = struct.unpack("<f", value)[0]
    return tuple(coordinates)


def parse_segment(
    path: Path, wanted_ids: set[str] | None = None
) -> list[tuple[int, dict[str, tuple[float | None, float | None, float | None]]]]:
    data = path.read_bytes()
    output = []
    offset = 0
    while offset + 4 <= len(data):
        (frame_length,) = struct.unpack("<I", data[offset : offset + 4])
        offset += 4
        frame = data[offset : offset + frame_length]
        if len(frame) != frame_length:
            raise ValueError(f"truncated frame in {path} at byte {offset}")
        offset += frame_length
        timestamp = None
        entities = {}
        for field_number, wire_type, value in fields(frame):
            if field_number == 1 and wire_type == 0:
                timestamp = value
            elif field_number == 2 and wire_type == 2:
                entity_id = None
                position = None
                for entity_field, entity_wire, entity_value in fields(value):
                    if entity_field == 1 and entity_wire == 2:
                        entity_id = entity_value.decode("utf-8", "replace")
                    elif entity_field == 3 and entity_wire == 2:
                        position = parse_position(entity_value)
                if entity_id is not None and position is not None:
                    if wanted_ids is None or entity_id in wanted_ids:
                        entities[entity_id] = position
        if timestamp is None:
            raise ValueError(f"frame without timestamp in {path}")
        output.append((timestamp, entities))
    if offset != len(data):
        raise ValueError(f"trailing bytes in {path}")
    return output
