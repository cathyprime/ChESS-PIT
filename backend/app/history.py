from sqlalchemy import func, or_, select

from .models import Bot, Game
from .avatars import avatar_style_for_bot, avatar_url


def outcome_for(game: Game, bot_id: int) -> str:
    if game.result == "1/2-1/2":
        return "draw"
    if game.result in ("1-0", "0-1"):
        bot_won = ((game.white_bot_id == bot_id and game.result == "1-0") or
                   (game.black_bot_id == bot_id and game.result == "0-1"))
        return "win" if bot_won else "loss"
    if game.status in ("queued", "running"):
        return "pending"
    return "no-result"


def history_game_json(db, game: Game, bot_id: int) -> dict:
    bot_is_white = game.white_bot_id == bot_id
    opponent_id = game.black_bot_id if bot_is_white else game.white_bot_id
    opponent_name = game.black_name if bot_is_white else game.white_name
    opponent = db.get(Bot, opponent_id) if opponent_id else None
    return {
        "id": game.id,
        "mode": game.mode,
        "status": game.status,
        "whiteName": game.white_name,
        "blackName": game.black_name,
        "result": game.result,
        "termination": game.termination,
        "timeControl": game.time_control,
        "createdAt": game.created_at,
        "botColor": "white" if bot_is_white else "black",
        "opponentId": opponent_id,
        "opponentName": opponent_name,
        "opponentAvatarUrl": avatar_url(opponent_id, opponent_name),
        "opponentAvatarStyle": avatar_style_for_bot(opponent, opponent_name),
        "outcome": outcome_for(game, bot_id),
    }


def bot_history_page(db, bot: Bot, offset: int, limit: int) -> dict:
    linked = or_(Game.white_bot_id == bot.id, Game.black_bot_id == bot.id)
    total = int(db.scalar(select(func.count(Game.id)).where(Game.deleted == False, linked)) or 0)
    games = list(db.scalars(select(Game).where(Game.deleted == False, linked)
                            .order_by(Game.id.desc()).offset(offset).limit(limit)))
    return {"total": total, "games": [history_game_json(db, game, bot.id) for game in games]}
