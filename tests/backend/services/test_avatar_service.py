"""Przetwarzanie i zapis awatarów (SR-9, T-10)."""

from __future__ import annotations

import os
import stat
from io import BytesIO

import pytest
from PIL import Image

from backend.core.constants import AVATAR_SIZE
from backend.core.extensions import db
from backend.services import avatar_service
from backend.services.avatar_service import AvatarService, InvalidAvatarError, process_image


def _decode(content: bytes) -> Image.Image:
    image = Image.open(BytesIO(content))
    image.load()
    return image


class TestProcessImage:
    @pytest.mark.parametrize(("image_format", "extension"), [("PNG", "png"), ("JPEG", "jpg")])
    def test_accepts_png_and_jpeg(self, image_bytes, image_format: str, extension: str) -> None:
        content, ext = process_image(BytesIO(image_bytes(image_format)))

        assert ext == extension
        assert _decode(content).format == image_format

    def test_shrinks_to_avatar_size_keeping_proportions(self, image_bytes) -> None:
        content, _ = process_image(BytesIO(image_bytes("PNG", (1000, 500))))

        assert _decode(content).size == (AVATAR_SIZE, AVATAR_SIZE // 2)

    def test_keeps_png_transparency(self, image_bytes) -> None:
        content, _ = process_image(BytesIO(image_bytes("PNG", mode="RGBA")))

        assert _decode(content).mode == "RGBA"

    def test_converts_palette_png(self, image_bytes) -> None:
        content, _ = process_image(BytesIO(image_bytes("PNG", mode="P")))

        assert _decode(content).mode == "RGBA"

    def test_strips_exif_metadata(self, image_bytes) -> None:
        exif = Image.Exif()
        exif[0x010F] = "Aparat"  # Make
        exif[0x9286] = "Komentarz z lokalizacją"  # UserComment

        content, _ = process_image(BytesIO(image_bytes("JPEG", exif=exif.tobytes())))

        assert dict(_decode(content).getexif()) == {}

    def test_applies_exif_orientation(self, image_bytes) -> None:
        exif = Image.Exif()
        exif[0x0112] = 6  # Orientation: obrót o 90 stopni

        content, _ = process_image(BytesIO(image_bytes("JPEG", (40, 20), exif=exif.tobytes())))

        assert _decode(content).size == (20, 40)

    @pytest.mark.parametrize(
        "content",
        [b"", b"<svg xmlns='http://www.w3.org/2000/svg'/>", b"<html></html>", b"\x89PNG\r\n\x1a\n" + b"\x00" * 20],
    )
    def test_rejects_non_images_and_broken_files(self, content: bytes) -> None:
        with pytest.raises(InvalidAvatarError):
            process_image(BytesIO(content))

    def test_rejects_other_image_formats(self, image_bytes) -> None:
        with pytest.raises(InvalidAvatarError, match="PNG i JPEG"):
            process_image(BytesIO(image_bytes("GIF")))

    def test_rejects_truncated_png(self, image_bytes) -> None:
        data = image_bytes("PNG", (200, 200))

        with pytest.raises(InvalidAvatarError):
            process_image(BytesIO(data[: len(data) // 2]))

    def test_rejects_decompression_bomb(self, image_bytes, monkeypatch) -> None:
        monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 100)

        for size in [(11, 11), (30, 30)]:  # powyżej limitu (ostrzeżenie) i powyżej dwukrotności (błąd)
            with pytest.raises(InvalidAvatarError, match="rozdzielczość"):
                process_image(BytesIO(image_bytes("PNG", size)))


class TestAvatarService:
    def test_save_and_delete(self, make_user, avatar_dir, image_bytes) -> None:
        user = make_user()
        service = AvatarService(avatar_dir)

        filename = service.save(user, BytesIO(image_bytes("PNG")))

        assert user.avatar_filename == filename
        assert (avatar_dir / filename).is_file()
        assert not list(avatar_dir.glob("*.tmp"))

        service.delete(user)

        assert user.avatar_filename is None
        assert not (avatar_dir / filename).exists()

    @pytest.mark.skipif(os.name == "nt", reason="Windows nie obsługuje uprawnień POSIX")
    def test_saved_file_is_readable_by_others(self, make_user, avatar_dir, image_bytes) -> None:
        filename = AvatarService(avatar_dir).save(make_user(), BytesIO(image_bytes("PNG")))

        assert stat.S_IMODE((avatar_dir / filename).stat().st_mode) == 0o644

    def test_delete_without_avatar_is_a_no_op(self, make_user, avatar_dir) -> None:
        AvatarService(avatar_dir).delete(make_user())

    def test_never_deletes_files_outside_pattern(self, make_user, avatar_dir, tmp_path, image_bytes) -> None:
        secret = tmp_path / "secret.txt"
        secret.write_text("nie usuwać", encoding="utf-8")
        user = make_user(avatar_filename="../secret.txt")

        AvatarService(avatar_dir).save(user, BytesIO(image_bytes("PNG")))

        assert secret.exists()

    def test_failed_commit_removes_new_file(self, make_user, avatar_dir, image_bytes, monkeypatch) -> None:
        user = make_user()

        def broken_commit() -> None:
            raise RuntimeError("baza niedostępna")

        monkeypatch.setattr(db.session, "commit", broken_commit)
        with pytest.raises(RuntimeError):
            AvatarService(avatar_dir).save(user, BytesIO(image_bytes("PNG")))

        assert not any(avatar_dir.iterdir())

    def test_failed_write_leaves_no_temporary_file(self, make_user, avatar_dir, image_bytes, monkeypatch) -> None:
        user = make_user()

        def broken_replace(*_args) -> None:
            raise OSError("dysk pełny")

        monkeypatch.setattr(avatar_service.os, "replace", broken_replace)
        with pytest.raises(OSError):
            AvatarService(avatar_dir).save(user, BytesIO(image_bytes("PNG")))

        assert not any(avatar_dir.iterdir())
        assert user.avatar_filename is None

    def test_rejected_file_is_logged(self, make_user, avatar_dir, caplog) -> None:
        make_user()
        with caplog.at_level("INFO", logger="flatmate.security"), pytest.raises(InvalidAvatarError):
            AvatarService(avatar_dir).save(make_user(), BytesIO(b"nie obraz"))

        assert '"avatar_rejected"' in caplog.text


def test_pillow_pixel_limit_is_configured() -> None:
    assert Image.MAX_IMAGE_PIXELS == avatar_service.AVATAR_MAX_PIXELS
