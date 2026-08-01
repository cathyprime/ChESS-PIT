import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.history import bot_history_page, outcome_for
from app.models import Bot, Game


class BotHistoryTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                                    poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine, expire_on_commit=False)()
        self.bot = self.make_bot("Current name")
        self.opponent = self.make_bot("Opponent")
        self.unrelated = self.make_bot("Unrelated")

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def make_bot(self, name):
        bot = Bot(name=name, binary_path="/engine", sha256="0" * 64, owner_id="owner",
                  recovery_hash="", status="active", engine_kind="uploaded")
        self.db.add(bot)
        self.db.flush()
        return bot

    def game(self, white_id, black_id, white_name, black_name, result,
             *, mode="rated", status="completed", deleted=False):
        game = Game(mode=mode, status=status, white_bot_id=white_id, black_bot_id=black_id,
                    white_name=white_name, black_name=black_name, result=result,
                    time_control="10+0.1", deleted=deleted)
        self.db.add(game)
        self.db.flush()
        return game

    def test_outcomes_are_from_selected_bot_perspective(self):
        white_win = self.game(self.bot.id, self.opponent.id, "Old name", "Opponent", "1-0")
        black_loss = self.game(self.opponent.id, self.bot.id, "Opponent", "Old name", "1-0")
        draw = self.game(self.bot.id, self.opponent.id, "Old name", "Opponent", "1/2-1/2")
        pending = self.game(self.bot.id, self.opponent.id, "Old name", "Opponent", "*", status="running")
        failed = self.game(self.bot.id, self.opponent.id, "Old name", "Opponent", "*", status="failed")

        self.assertEqual(outcome_for(white_win, self.bot.id), "win")
        self.assertEqual(outcome_for(black_loss, self.bot.id), "loss")
        self.assertEqual(outcome_for(draw, self.bot.id), "draw")
        self.assertEqual(outcome_for(pending, self.bot.id), "pending")
        self.assertEqual(outcome_for(failed, self.bot.id), "no-result")

    def test_history_filters_by_stable_id_and_paginates_newest_first(self):
        first = self.game(self.bot.id, self.opponent.id, "Old name", "Opponent", "1-0")
        second = self.game(None, self.bot.id, "Human", "Old name", "0-1", mode="human")
        self.game(self.unrelated.id, self.opponent.id, "Unrelated", "Opponent", "1-0")
        self.game(self.bot.id, self.opponent.id, "Old name", "Opponent", "1/2-1/2", deleted=True)
        self.bot.name = "Renamed bot"
        self.db.commit()

        newest = bot_history_page(self.db, self.bot, 0, 1)
        older = bot_history_page(self.db, self.bot, 1, 1)

        self.assertEqual(newest["total"], 2)
        self.assertEqual(newest["games"][0]["id"], second.id)
        self.assertEqual(newest["games"][0]["opponentName"], "Human")
        self.assertIsNone(newest["games"][0]["opponentId"])
        self.assertEqual(older["games"][0]["id"], first.id)


if __name__ == "__main__":
    unittest.main()
