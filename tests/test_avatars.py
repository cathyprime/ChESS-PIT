import io
import unittest

from PIL import Image

from app.avatars import (MAX_AVATAR_BYTES, avatar_path_for, avatar_style_for_bot, avatar_url,
                         avatar_url_for_bot, stockfish_asset, validate_avatar)
from app.models import Bot


def png(width=128, height=128, color=(40, 90, 150, 255), transparent=True):
    output = io.BytesIO()
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0) if transparent else color)
    if transparent:
        image.paste(color, (24, 12, width - 24, height - 12))
    image.save(output, format="PNG")
    return output.getvalue()


class AvatarTests(unittest.TestCase):
    def bot(self, *, kind="uploaded", skill=None, path=None):
        return Bot(id=7, name="Fixture", binary_path="/engine", sha256="0" * 64,
                   owner_id="owner", recovery_hash="", status="active",
                   engine_kind=kind, stockfish_skill=skill, avatar_path=path)

    def test_valid_png_is_canonical_128_rgba(self):
        encoded, digest = validate_avatar(png())
        with Image.open(io.BytesIO(encoded)) as image:
            self.assertEqual(image.size, (128, 128))
            self.assertEqual(image.mode, "RGBA")
        self.assertEqual(len(digest), 64)

    def test_rejects_wrong_dimensions_format_and_size(self):
        with self.assertRaisesRegex(ValueError, "exactly 128×128"):
            validate_avatar(png(64, 128))
        jpeg = io.BytesIO()
        Image.new("RGB", (128, 128)).save(jpeg, format="JPEG")
        with self.assertRaisesRegex(ValueError, "PNG"):
            validate_avatar(jpeg.getvalue())
        with self.assertRaisesRegex(ValueError, "256 KB"):
            validate_avatar(b"x" * (MAX_AVATAR_BYTES + 1))

    def test_rejects_animated_png(self):
        output = io.BytesIO()
        frames = [Image.new("RGBA", (128, 128), color) for color in ("red", "blue")]
        frames[0].save(output, format="PNG", save_all=True, append_images=frames[1:], duration=100)
        with self.assertRaisesRegex(ValueError, "Animated"):
            validate_avatar(output.getvalue())

    def test_rejects_opaque_square_avatar(self):
        with self.assertRaisesRegex(ValueError, "transparent background"):
            validate_avatar(png(transparent=False))

    def test_resolves_default_stockfish_and_generic_urls(self):
        self.assertEqual(avatar_path_for(self.bot()).name, "default-bot.png")
        self.assertEqual(avatar_path_for(self.bot(kind="stockfish", skill=13)).name,
                         "stockfish-13.png")
        self.assertEqual(avatar_url(7), "/api/bots/7/avatar")
        self.assertEqual(avatar_url_for_bot(self.bot()), "/api/bots/7/avatar?v=default")
        self.assertEqual(avatar_url(None, "Stockfish"), "/api/avatars/stockfish/full")
        self.assertIsNone(avatar_url(None, "Human"))
        self.assertEqual(avatar_style_for_bot(self.bot()), "legacy")
        self.assertEqual(avatar_style_for_bot(self.bot(kind="stockfish", skill=13)), "mask")
        self.assertEqual(avatar_style_for_bot(None, "Stockfish"), "mask")

    def test_resolves_themed_benchmark_masks_and_rejects_unknown_themes(self):
        themed = stockfish_asset(20, "catppuccin")
        self.assertEqual(themed.parent.name, "catppuccin")
        self.assertEqual(themed.name, "stockfish-20.png")
        self.assertTrue(themed.is_file())
        self.assertEqual(avatar_path_for(self.bot(kind="stockfish", skill=5), "emo").parent.name,
                         "emo")
        self.assertEqual(stockfish_asset(20, "../../escape").parent.name, "inferno")


if __name__ == "__main__":
    unittest.main()
