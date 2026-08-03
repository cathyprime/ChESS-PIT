from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import ArenaSetting, Bot, Game, RatingEvent, RatingRun
from app.runner import (
    DEFAULT_RATING_TIME_CONTROL,
    cancel_current_rating_run,
    missing_pairings,
    normalize_rating_time_control,
    options_for_bot,
    rating_time_controls,
    recount,
    stockfish_description,
)


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

    def test_rating_time_controls_are_fastchess_second_based_presets(self):
        self.assertEqual(
            [control["value"] for control in rating_time_controls()],
            ["1+0", "2+0.02", "3+0.03", "5+0.05", "10+0.1", "15+0.1",
             "30+0.3", "60+0.6", "120+1"],
        )
        self.assertEqual(normalize_rating_time_control("60+0.6"), "60+0.6")
        self.assertEqual(normalize_rating_time_control("999+999"), DEFAULT_RATING_TIME_CONTROL)

    def test_recount_uses_saved_k_factor(self):
        first, second = self.bot("First"), self.bot("Second")
        self.game(first, second, "1-0")
        setting = ArenaSetting(key="k_factor", value="32")
        self.db.add(setting)
        self.db.commit()

        recount(self.db)
        self.assertEqual(first.rating, 1516.0)
        self.assertEqual(second.rating, 1484.0)

        setting.value = "16"
        self.db.commit()
        recount(self.db)
        self.assertEqual(first.rating, 1508.0)
        self.assertEqual(second.rating, 1492.0)

    def test_cancel_rating_run_stops_queued_work_or_marks_running_work(self):
        queued = RatingRun(status="queued", current_pairing="First vs Second")
        self.db.add(queued)
        self.db.commit()

        with patch("app.runner.SessionLocal", self.Session):
            cancelled = cancel_current_rating_run()

        self.assertEqual(cancelled.status, "cancelled")
        self.assertIsNone(cancelled.current_pairing)
        self.assertIsNotNone(cancelled.completed_at)

        running = RatingRun(status="running", current_pairing="Second vs Third")
        self.db.add(running)
        self.db.commit()

        with patch("app.runner.SessionLocal", self.Session):
            cancelling = cancel_current_rating_run()

        self.assertEqual(cancelling.status, "cancelling")
        self.assertEqual(cancelling.current_pairing, "Second vs Third")

    def test_stockfish_fastchess_options_include_skill_level(self):
        bot = self.bot("Stockfish Level 13", "stockfish", 13)

        options = options_for_bot(bot)

        self.assertIn("name=Stockfish Level 13", options)
        self.assertIn("option.Skill Level=13", options)

    def test_stockfish_description_is_stable_for_benchmarks(self):
        self.assertIn("High-strength Stockfish", stockfish_description(20))
        self.assertIn("Skill Level 7", stockfish_description(7))


if __name__ == "__main__":
    unittest.main()
