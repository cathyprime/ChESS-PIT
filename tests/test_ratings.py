from datetime import datetime, timedelta, timezone
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import ArenaSetting, Bot, Game, RatingEvent
from app.runner import missing_pairings, options_for_bot, recount


class RatingTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                                    poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def bot(self, name, kind="uploaded", skill=None):
        bot = Bot(name=name, binary_path="/engine", sha256="0" * 64, owner_id="owner",
                  recovery_hash="", status="active", engine_kind=kind, stockfish_skill=skill)
        self.db.add(bot)
        self.db.flush()
        return bot

    def game(self, white, black, result, *, deleted=False, seconds=0):
        game = Game(mode="rated", status="completed", white_bot_id=white.id,
                    black_bot_id=black.id, white_name=white.name, black_name=black.name,
                    result=result, deleted=deleted,
                    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds))
        self.db.add(game)
        return game

    def test_recount_uses_valid_games_and_preserves_later_adjustment(self):
        first, second = self.bot("First"), self.bot("Second")
        self.game(first, second, "1-0", seconds=1)
        self.game(second, first, "1-0", deleted=True, seconds=2)
        self.db.add(RatingEvent(bot_id=first.id, value=1600, reason="fixture",
                                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=3)))
        self.db.commit()

        result = recount(self.db)

        self.assertEqual(result["gamesProcessed"], 1)
        self.assertEqual(first.rating, 1600)
        self.assertEqual((first.wins, first.draws, first.losses), (1, 0, 0))
        self.assertEqual((second.wins, second.draws, second.losses), (0, 0, 1))
        self.assertEqual({change["botId"] for change in result["changes"]}, {first.id, second.id})

    def test_missing_pairings_only_returns_deficits(self):
        first, second, third = self.bot("First"), self.bot("Second"), self.bot("Third")
        self.db.add(ArenaSetting(key="games_per_pair", value="2"))
        self.game(first, second, "1/2-1/2", seconds=1)
        self.game(second, first, "1/2-1/2", seconds=2)
        self.db.commit()

        missing = missing_pairings(self.db)

        self.assertEqual({(row[0], row[1], row[2]) for row in missing},
                         {(first.id, third.id, 2), (second.id, third.id, 2)})

    def test_stockfish_fastchess_options_include_skill_level(self):
        bot = self.bot("Stockfish Level 13", "stockfish", 13)

        options = options_for_bot(bot)

        self.assertIn("name=Stockfish Level 13", options)
        self.assertIn("option.Skill Level=13", options)


if __name__ == "__main__":
    unittest.main()
