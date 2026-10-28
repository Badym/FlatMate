"""Awatary użytkowników (SR-9, T-10).

Plik jest sprawdzany po zawartości, a nie po rozszerzeniu: Pillow musi go
rozpoznać jako PNG albo JPEG. Obraz jest dekodowany, zmniejszany i zapisywany
od nowa, więc z pliku znikają metadane (EXIF z lokalizacją) i ewentualny
dołączony kod. Nazwa pliku jest losowa, a stary awatar jest usuwany.
"""

from __future__ import annotations

import os
import re
import secrets
import tempfile
import warnings
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from PIL import Image, ImageOps, UnidentifiedImageError

from backend.audit import audit_event
from backend.core.constants import AVATAR_MAX_PIXELS, AVATAR_SIZE
from backend.core.extensions import db
from backend.models import User

ALLOWED_FORMATS = {"PNG": "png", "JPEG": "jpg"}
AVATAR_FILENAME_PATTERN = re.compile(r"[0-9a-f]{32}\.(png|jpg)")
AVATAR_URL_PREFIX = "uploads/avatars/"
AVATAR_FILE_MODE = 0o644

# Pillow ostrzega powyżej limitu i przerywa powyżej dwukrotności; ostrzeżenie zamieniamy na błąd.
Image.MAX_IMAGE_PIXELS = AVATAR_MAX_PIXELS


class InvalidAvatarError(ValueError):
    """Plik nie jest dopuszczalnym obrazem; komunikat jest przeznaczony dla użytkownika."""


def process_image(stream: BinaryIO) -> tuple[bytes, str]:
    """Zwraca (bajty nowego pliku, rozszerzenie) albo zgłasza InvalidAvatarError."""
    data = stream.read()
    if not data:
        raise InvalidAvatarError("Wybierz plik obrazu.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as probe:
                image_format = probe.format
                probe.verify()
            if image_format not in ALLOWED_FORMATS:
                raise InvalidAvatarError("Dozwolone są tylko obrazy PNG i JPEG.")
            # Po verify() obiekt nie nadaje się do użycia, więc otwieramy plik ponownie.
            with Image.open(BytesIO(data)) as image:
                image = ImageOps.exif_transpose(image)
                image.thumbnail((AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS)
                return _encode(image, image_format), ALLOWED_FORMATS[image_format]
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise InvalidAvatarError("Obraz ma zbyt dużą rozdzielczość.") from exc
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        if isinstance(exc, InvalidAvatarError):
            raise
        raise InvalidAvatarError("Dozwolone są tylko obrazy PNG i JPEG.") from exc


def _encode(image: Image.Image, image_format: str) -> bytes:
    output = BytesIO()
    if image_format == "JPEG":
        image.convert("RGB").save(output, format="JPEG", quality=90, optimize=True)
    else:
        if image.mode not in {"RGB", "RGBA", "L", "LA"}:
            image = image.convert("RGBA")
        image.save(output, format="PNG", optimize=True)
    return output.getvalue()


class AvatarService:
    def __init__(self, upload_dir: Path) -> None:
        self._upload_dir = Path(upload_dir)

    def save(self, user: User, stream: BinaryIO) -> str:
        try:
            content, extension = process_image(stream)
        except InvalidAvatarError as exc:
            audit_event("avatar_rejected", reason=str(exc))
            raise
        filename = f"{secrets.token_hex(16)}.{extension}"
        self._write_atomically(filename, content)

        previous = user.avatar_filename
        user.avatar_filename = filename
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            self._remove(filename)
            raise
        self._remove(previous)
        audit_event("avatar_updated")
        return filename

    def delete(self, user: User) -> None:
        previous = user.avatar_filename
        if previous is None:
            return
        user.avatar_filename = None
        db.session.commit()
        self._remove(previous)
        audit_event("avatar_removed")

    def _write_atomically(self, filename: str, content: bytes) -> None:
        self._upload_dir.mkdir(parents=True, exist_ok=True)
        descriptor, temp_path = tempfile.mkstemp(dir=self._upload_dir, suffix=".tmp")
        try:
            with os.fdopen(descriptor, "wb") as temp_file:
                temp_file.write(content)
            # mkstemp tworzy plik 0600; awatar to plik publiczny, czytany też np. przez proxy (etap 9).
            os.chmod(temp_path, AVATAR_FILE_MODE)
            os.replace(temp_path, self._upload_dir / filename)
        except BaseException:
            Path(temp_path).unlink(missing_ok=True)
            raise

    def _remove(self, filename: str | None) -> None:
        # Nazwa z bazy musi pasować do wzorca, więc nie da się wskazać pliku poza katalogiem.
        if filename and AVATAR_FILENAME_PATTERN.fullmatch(filename):
            (self._upload_dir / filename).unlink(missing_ok=True)
