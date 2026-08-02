import { useEffect, useMemo, useRef, useState } from "react";
import {
  BrowserRouter,
  Link,
  NavLink,
  Navigate,
  Route,
  Routes,
  useNavigate,
  useParams,
} from "./router";
import { Chess } from "chess.js";
import { api } from "./api";
import { ArenaBoard } from "./Board";
import { BotAvatar } from "./Avatar";
import { THEMES, THEME_IDS, themeArt, useTheme } from "./theme";
import type {
  Analysis,
  AvatarStyle,
  Bot,
  BotHistoryResponse,
  Game,
  HistoryGame,
  RatingRun,
} from "./types";
import "./style.css";
import "./admin.css";
import "./live.css";
import "./themes.css";

type EffectMode = "unset" | "full" | "static";
const EFFECTS_KEY = "deathpit-effects";
const SITE_NAME = "DeathPit";
function savedEffects(): EffectMode {
  const value = localStorage.getItem(EFFECTS_KEY);
  return value === "full" || value === "static" ? value : "unset";
}
function ThemeDecor() {
  const { theme } = useTheme();
  return (
    <div className="inferno-decor" aria-hidden="true">
      <img
        className="invader reaper-invader"
        src={themeArt(theme.id, "decor", "reaper")}
        alt=""
      />
      <img
        className="invader scythe-invader"
        src={themeArt(theme.id, "decor", "emblem")}
        alt=""
      />
      <img
        className="invader hand-invader"
        src={themeArt(theme.id, "decor", "hand")}
        alt=""
      />
    </div>
  );
}
function AppearanceMenu({
  open,
  firstRun,
  effects,
  onEffects,
  onClose,
}: {
  open: boolean;
  firstRun: boolean;
  effects: EffectMode;
  onEffects: (mode: "full" | "static") => void;
  onClose: () => void;
}) {
  const { theme, setTheme } = useTheme();
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!open) return null;
  return (
    <div
      className="effects-warning appearance-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="appearance-title"
    >
      <div className="effects-warning-card appearance-card">
        {!firstRun && (
          <button
            className="appearance-close ghost"
            aria-label="Close appearance menu"
            onClick={onClose}
          >
            ×
          </button>
        )}
        <span className="warning-skull">{theme.symbol}</span>
        <span className="eyebrow">DEATHPIT APPEARANCE</span>
        <h1 id="appearance-title">Choose your underworld</h1>
        <p>
          Every realm changes the arena art, language, benchmark masks, and
          chessboard. Your choice stays on this device.
        </p>
        <div className="theme-grid">
          {THEME_IDS.map((id) => {
            const option = THEMES[id];
            return (
              <button
                type="button"
                className={`theme-choice theme-choice-${id} ${theme.id === id ? "selected" : ""}`}
                aria-pressed={theme.id === id}
                onClick={() => setTheme(id)}
                key={id}
              >
                <i>{option.symbol}</i>
                <span>
                  <strong>{option.label}</strong>
                  <small>{option.description}</small>
                </span>
              </button>
            );
          })}
        </div>
        <div className="motion-controls">
          <div>
            <strong>Lettering motion</strong>
            <small>
              {reduced
                ? "Your device requests reduced motion. Static is recommended."
                : "Only text effects and the skeletal hand can move."}
            </small>
          </div>
          <button
            className={effects === "full" ? "selected" : ""}
            onClick={() => onEffects("full")}
          >
            Alive
          </button>
          <button
            className={effects === "static" ? "selected" : ""}
            autoFocus={firstRun && reduced}
            onClick={() => onEffects("static")}
          >
            Still
          </button>
        </div>
        {firstRun && (
          <button
            className="appearance-enter"
            onClick={() => {
              onEffects(
                effects === "unset" ? (reduced ? "static" : "full") : effects,
              );
              onClose();
            }}
          >
            Enter {theme.label}
          </button>
        )}
      </div>
    </div>
  );
}

function Login({ done }: { done: () => void }) {
  const { theme } = useTheme();
  const [password, setPassword] = useState("fightclub");
  const [error, setError] = useState("");
  return (
    <main className="login">
      <div className="card">
        <span className="eyebrow">{theme.copy.login.eyebrow}</span>
        <h1>{SITE_NAME}</h1>
        <p>{theme.copy.login.body}</p>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            try {
              await api("/api/auth/login", {
                method: "POST",
                body: JSON.stringify({ password }),
              });
              done();
            } catch (x: any) {
              setError(x.message);
            }
          }}
        >
          <label>
            {theme.copy.login.password}
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoFocus
            />
          </label>
          <button>{theme.copy.login.enter}</button>
          {error && <p className="error">{error}</p>}
        </form>
      </div>
    </main>
  );
}

function Header({ bots, refresh }: { bots: Bot[]; refresh: () => void }) {
  const { theme } = useTheme();
  return (
    <>
      <header>
        <Link className="brand" to="/" aria-label={`${SITE_NAME} home`}>
          <span className="brand-mark" aria-hidden="true">
            {theme.symbol}
          </span>
          <span className="brand-name">{SITE_NAME}</span>
        </Link>
        <nav>
          <NavLink to="/">{theme.copy.nav.arena}</NavLink>
          <NavLink to="/games">{theme.copy.nav.games}</NavLink>
          <NavLink to="/upload">{theme.copy.nav.upload}</NavLink>
          <NavLink to="/rules">{theme.copy.nav.rules}</NavLink>
        </nav>
        <Admin bots={bots} refresh={refresh} />
      </header>
      <div
        className="site-banner"
        role="img"
        aria-label={`${theme.label} DeathPit chess arena banner`}
      >
        <div>
          <strong>{SITE_NAME}</strong>
          <span>{theme.copy.tagline}</span>
        </div>
      </div>
    </>
  );
}

function RulesPage() {
  const { theme } = useTheme();
  return (
    <main className="shell route-rules rules-page">
      <span className="eyebrow">{theme.copy.rules.eyebrow}</span>
      <h1>{theme.copy.rules.title}</h1>
      <div className="rules-card">
        <span className="rule-skull">{theme.symbol}</span>
        <ol>
          <li>Do not talk about the death pit.</li>
          <li>Do not talk about the death pit.</li>
        </ol>
        <p>{theme.copy.rules.footer}</p>
      </div>
    </main>
  );
}

function Leaderboard({ bots }: { bots: Bot[] }) {
  const { theme } = useTheme();
  const copy = theme.copy.ladder;
  const [showBenchmarks, setShowBenchmarks] = useState(true);
  const visibleBots = showBenchmarks ? bots : bots.filter((bot) => !bot.system);
  let rank = 0;
  return (
    <section className="leaderboard-section">
      <div className="table-wrap">
        <div className="leaderboard-head">
          <div className="leaderboard-heading">
            <span className="eyebrow">{copy.eyebrow}</span>
            <h2>{copy.title}</h2>
          </div>
          <button
            type="button"
            className="secondary benchmark-toggle"
            aria-pressed={!showBenchmarks}
            onClick={() => setShowBenchmarks((current) => !current)}
          >
            {showBenchmarks ? copy.hide : copy.show}
          </button>
        </div>
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Bot</th>
              <th>Elo</th>
              <th>Record</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {visibleBots.map((b) => {
              if (b.status === "active") rank++;
              return (
                <tr key={b.id}>
                  <td>{b.status === "active" ? rank : "—"}</td>
                  <td>
                    <div className="identity-cell">
                      <BotAvatar
                        src={b.avatarUrl}
                        name={b.name}
                        style={b.avatarStyle}
                      />
                      <div>
                        <Link className="bot-link" to={`/bots/${b.id}`}>
                          <strong>{b.name}</strong>
                        </Link>
                        {b.system && (
                          <span className="tag system-tag">benchmark</span>
                        )}
                        {b.owned && <span className="tag">yours</span>}
                        {b.description && (
                          <p className="bot-description">{b.description}</p>
                        )}
                        <small>{b.failureReason}</small>
                      </div>
                    </div>
                  </td>
                  <td className="rating">
                    {b.status === "active" ? b.rating.toFixed(1) : "—"}
                  </td>
                  <td>
                    {b.wins}-{b.draws}-{b.losses}
                  </td>
                  <td>
                    <span className={"status " + b.status}>{b.status}</span>
                    {b.status === "qualifying" && (
                      <small>
                        {b.qualificationDone}/{b.qualificationTotal}
                      </small>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {!visibleBots.length && <p className="empty">{copy.empty}</p>}
      </div>
    </section>
  );
}

async function avatarError(file: File) {
  if (file.type && file.type !== "image/png")
    return "Mask must be a PNG image.";
  if (file.size > 256 * 1024) return "Mask must be 256 KB or smaller.";
  const url = URL.createObjectURL(file);
  try {
    const image = await new Promise<HTMLImageElement>((resolve, reject) => {
      const next = new Image();
      next.onload = () => resolve(next);
      next.onerror = reject;
      next.src = url;
    });
    if (image.naturalWidth !== 128 || image.naturalHeight !== 128)
      return "Mask must be exactly 128×128 pixels.";
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = 128;
    const context = canvas.getContext("2d");
    if (!context) return "This browser cannot validate the mask.";
    context.drawImage(image, 0, 0);
    const pixels = context.getImageData(0, 0, 128, 128).data;
    let transparent = 0;
    for (let index = 3; index < pixels.length; index += 4)
      if (pixels[index] === 0) transparent++;
    return transparent >= 1638
      ? ""
      : "Mask needs a transparent background (at least 10% fully transparent).";
  } catch {
    return "Mask is not a valid PNG image.";
  } finally {
    URL.revokeObjectURL(url);
  }
}

function Dashboard({ bots, refresh }: { bots: Bot[]; refresh: () => void }) {
  const { theme } = useTheme();
  const mine = bots.filter((b) => b.owned);
  const replace = async (bot: Bot, file?: File) => {
    if (!file) return;
    const error = await avatarError(file);
    if (error) {
      alert(error);
      return;
    }
    const data = new FormData();
    data.append("avatar", file);
    try {
      await api(`/api/bots/${bot.id}/avatar`, { method: "PUT", body: data });
      refresh();
    } catch (reason: any) {
      alert(reason.message);
    }
  };
  const updateDescription = async (bot: Bot) => {
    const description = prompt(
      "Bot description (max 280 characters)",
      bot.description || "",
    );
    if (description === null) return;
    try {
      await api(`/api/bots/${bot.id}`, {
        method: "PATCH",
        body: JSON.stringify({ description }),
      });
      refresh();
    } catch (reason: any) {
      alert(reason.message);
    }
  };
  const actions = theme.copy.actions;
  return (
    <main className="shell route-arena">
      <div className="arena-layout">
        <section className="leaderboard-panel">
          <Leaderboard bots={bots} />
        </section>
        <aside className="arena-actions">
          <Link className="action-card showdown" to="/showdown">
            <span>{actions.showdown.eyebrow}</span>
            <h2>{actions.showdown.title}</h2>
            <p>{actions.showdown.body}</p>
            <b>{actions.showdown.cta}</b>
          </Link>
          <Link className="action-card human-action" to="/play">
            <span>{actions.play.eyebrow}</span>
            <h2>{actions.play.title}</h2>
            <p>{actions.play.body}</p>
            <b>{actions.play.cta}</b>
          </Link>
        </aside>
      </div>
      {mine.length > 0 && (
        <section className="card manage-card">
          <h2>My bots</h2>
          {mine.map((b) => (
            <div className="manage" key={b.id}>
              <BotAvatar
                src={b.avatarUrl}
                name={b.name}
                style={b.avatarStyle}
              />
              <div className="manage-identity">
                <strong>{b.name}</strong>
                <p>{b.description || "No description provided."}</p>
              </div>
              <label className="file-button secondary">
                Forge new mask
                <input
                  type="file"
                  accept="image/png"
                  onChange={(event) => replace(b, event.target.files?.[0])}
                />
              </label>
              <button
                className="secondary"
                onClick={async () => {
                  const name = prompt("New name", b.name);
                  if (name) {
                    await api(`/api/bots/${b.id}`, {
                      method: "PATCH",
                      body: JSON.stringify({ name }),
                    });
                    refresh();
                  }
                }}
              >
                Rename
              </button>
              <button
                className="secondary"
                onClick={() => updateDescription(b)}
              >
                Edit bio
              </button>
              <button
                className="danger"
                onClick={async () => {
                  if (confirm(`Retire ${b.name}?`)) {
                    await api(`/api/bots/${b.id}`, { method: "DELETE" });
                    refresh();
                  }
                }}
              >
                Retire
              </button>
            </div>
          ))}
        </section>
      )}
    </main>
  );
}

type EngineChoice = {
  value: string;
  name: string;
  avatarUrl: string;
  avatarStyle: AvatarStyle;
};
function engineChoices(bots: Bot[]): EngineChoice[] {
  return [
    {
      value: "stockfish",
      name: "Stockfish 18",
      avatarUrl: "/api/avatars/stockfish/full",
      avatarStyle: "mask",
    },
    ...bots
      .filter((bot) => bot.status === "active")
      .map((bot) => ({
        value: String(bot.id),
        name: bot.name,
        avatarUrl: bot.avatarUrl,
        avatarStyle: bot.avatarStyle,
      })),
  ];
}
function EnginePicker({
  label,
  value,
  onChange,
  choices,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  choices: EngineChoice[];
}) {
  const [open, setOpen] = useState(false);
  const selected =
    choices.find((choice) => choice.value === value) || choices[0];
  useEffect(() => {
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    addEventListener("keydown", close);
    return () => removeEventListener("keydown", close);
  }, []);
  return (
    <div className="engine-picker">
      <span>{label}</span>
      <button
        type="button"
        className="engine-selected"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <BotAvatar
          src={selected?.avatarUrl}
          name={selected?.name || "Engine"}
          style={selected?.avatarStyle}
        />
        <strong>{selected?.name}</strong>
        <i>⌄</i>
      </button>
      {open && (
        <div className="engine-options" role="listbox" aria-label={label}>
          {choices.map((choice) => (
            <button
              type="button"
              role="option"
              aria-selected={choice.value === value}
              key={choice.value}
              onClick={() => {
                onChange(choice.value);
                setOpen(false);
              }}
            >
              <BotAvatar
                src={choice.avatarUrl}
                name={choice.name}
                style={choice.avatarStyle}
              />
              <span>{choice.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function ShowdownSetup({ bots }: { bots: Bot[] }) {
  const { theme } = useTheme();
  const copy = theme.copy.pages;
  const navigate = useNavigate();
  const active = bots.filter((b) => b.status === "active");
  const choices = engineChoices(bots);
  const [white, setWhite] = useState(active[0]?.id.toString() || "stockfish");
  const [black, setBlack] = useState(
    active[1]?.id.toString() || active[0]?.id.toString() || "stockfish",
  );
  const [tc, setTc] = useState("10+0.1");
  const [busy, setBusy] = useState(false);
  return (
    <main className="setup-shell route-showdown">
      <Link className="back" to="/">
        ← {theme.copy.nav.arena}
      </Link>
      <div className="card setup-card">
        <span className="eyebrow">{copy.showdownEyebrow}</span>
        <h1>{copy.showdown}</h1>
        <p>{copy.showdownBody}</p>
        <div className="versus">
          <EnginePicker
            label="White"
            value={white}
            onChange={setWhite}
            choices={choices}
          />
          <strong>VS</strong>
          <EnginePicker
            label="Black"
            value={black}
            onChange={setBlack}
            choices={choices}
          />
        </div>
        <label>
          Time control
          <select value={tc} onChange={(e) => setTc(e.target.value)}>
            <option value="1+0.01">Bullet · 1s + 0.01s</option>
            <option value="10+0.1">Fast · 10s + 0.1s</option>
            <option value="60+0.5">Long · 60s + 0.5s</option>
          </select>
        </label>
        <button
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            try {
              const game = await api<Game>("/api/exhibitions", {
                method: "POST",
                body: JSON.stringify({ white, black, time_control: tc }),
              });
              navigate(`/games/${game.id}`);
            } catch (x: any) {
              alert(x.message);
              setBusy(false);
            }
          }}
        >
          {busy ? "Starting engines…" : copy.startShowdown}
        </button>
      </div>
    </main>
  );
}

function HumanSetup({ bots }: { bots: Bot[] }) {
  const { theme } = useTheme();
  const copy = theme.copy.pages;
  const navigate = useNavigate();
  const [bot, setBot] = useState("stockfish");
  const [color, setColor] = useState("white");
  const [time, setTime] = useState(500);
  const [skill, setSkill] = useState(10);
  const [busy, setBusy] = useState(false);
  return (
    <main className="setup-shell route-play">
      <Link className="back" to="/">
        ← {theme.copy.nav.arena}
      </Link>
      <div className="card setup-card">
        <span className="eyebrow">{copy.playEyebrow}</span>
        <h1>{copy.play}</h1>
        <EnginePicker
          label="Opponent"
          value={bot}
          onChange={setBot}
          choices={engineChoices(bots)}
        />
        <div className="two">
          <label>
            Your color
            <select value={color} onChange={(e) => setColor(e.target.value)}>
              <option value="white">White</option>
              <option value="black">Black</option>
              <option value="random">Random</option>
            </select>
          </label>
          <label>
            Bot thinking time
            <select value={time} onChange={(e) => setTime(+e.target.value)}>
              <option value="100">100 ms</option>
              <option value="500">500 ms</option>
              <option value="1000">1 second</option>
              <option value="3000">3 seconds</option>
            </select>
          </label>
        </div>
        {bot === "stockfish" && (
          <label>
            Stockfish strength <span className="range-value">{skill}/20</span>
            <input
              type="range"
              min="0"
              max="20"
              value={skill}
              onChange={(e) => setSkill(+e.target.value)}
            />
          </label>
        )}
        <button
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            try {
              const game = await api<Game>("/api/human-games", {
                method: "POST",
                body: JSON.stringify({
                  bot,
                  human_color: color,
                  move_time_ms: time,
                  stockfish_skill: skill,
                }),
              });
              navigate(`/games/${game.id}`);
            } catch (x: any) {
              alert(x.message);
              setBusy(false);
            }
          }}
        >
          {busy ? "Preparing board…" : copy.startPlay}
        </button>
      </div>
    </main>
  );
}

function GameNames({ game }: { game: Game }) {
  return (
    <div className="game-identities">
      <span>
        {game.whiteAvatarUrl && (
          <BotAvatar
            src={game.whiteAvatarUrl}
            name={game.whiteName}
            style={game.whiteAvatarStyle}
          />
        )}
        <strong>{game.whiteName}</strong>
      </span>
      <i>vs</i>
      <span>
        {game.blackAvatarUrl && (
          <BotAvatar
            src={game.blackAvatarUrl}
            name={game.blackName}
            style={game.blackAvatarStyle}
          />
        )}
        <strong>{game.blackName}</strong>
      </span>
    </div>
  );
}
function GamesList() {
  const { theme } = useTheme();
  const copy = theme.copy.pages;
  const [games, setGames] = useState<Game[]>([]);
  useEffect(() => {
    api<Game[]>("/api/games").then(setGames);
  }, []);
  return (
    <main className="shell route-archive">
      <span className="eyebrow">{copy.gamesEyebrow}</span>
      <h1>{copy.games}</h1>
      <div className="game-list">
        {games.map((g) => (
          <Link className="game-row" to={`/games/${g.id}`} key={g.id}>
            <span>
              <GameNames game={g} />
              <small>
                {g.mode} · {g.timeControl}
              </small>
            </span>
            <b>{g.result}</b>
            <span className={"live-dot " + g.status}>{g.status}</span>
          </Link>
        ))}
        {!games.length && <p className="empty">{copy.gamesEmpty}</p>}
      </div>
    </main>
  );
}

const outcomeLabels: Record<HistoryGame["outcome"], string> = {
  win: "Win",
  draw: "Draw",
  loss: "Loss",
  pending: "In progress",
  "no-result": "No result",
};
function historyDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Unknown date" : date.toLocaleString();
}
function BotHistory() {
  const { theme } = useTheme();
  const { id } = useParams();
  const [page, setPage] = useState<BotHistoryResponse>();
  const [games, setGames] = useState<HistoryGame[]>([]);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    setBusy(true);
    setError("");
    setPage(undefined);
    setGames([]);
    api<BotHistoryResponse>(`/api/bots/${id}/games?offset=0&limit=50`)
      .then((value) => {
        if (active) {
          setPage(value);
          setGames(value.games);
          setBusy(false);
        }
      })
      .catch((reason) => {
        if (active) {
          setError(reason.message);
          setBusy(false);
        }
      });
    return () => {
      active = false;
    };
  }, [id]);
  const more = async () => {
    if (!page || busy) return;
    setBusy(true);
    setError("");
    try {
      const value = await api<BotHistoryResponse>(
        `/api/bots/${id}/games?offset=${games.length}&limit=50`,
      );
      setPage(value);
      setGames((current) => [...current, ...value.games]);
    } catch (reason: any) {
      setError(reason.message);
    } finally {
      setBusy(false);
    }
  };
  if (!page)
    return (
      <main className="shell bot-history route-history">
        <Link className="back" to="/">
          ← {theme.copy.ladder.title}
        </Link>
        {busy ? (
          <p className="empty">Loading bot history…</p>
        ) : (
          <div className="card">
            <h2>History unavailable</h2>
            <p className="error">{error}</p>
          </div>
        )}
      </main>
    );
  const bot = page.bot;
  return (
    <main className="shell bot-history route-history">
      <Link className="back" to="/">
        ← {theme.copy.ladder.title}
      </Link>
      <div className="bot-history-head">
        <div className="bot-history-identity">
          <BotAvatar
            src={bot.avatarUrl}
            name={bot.name}
            style={bot.avatarStyle}
          />
          <div>
            <span className="eyebrow">
              {theme.copy.pages.history.toUpperCase()}
            </span>
            <h1>{bot.name}</h1>
            <p className="bot-history-description">
              {bot.description || "No description provided."}
            </p>
            <div>
              {bot.system && <span className="tag system-tag">benchmark</span>}
              {bot.owned && <span className="tag">yours</span>}
              <span className={"status " + bot.status}>{bot.status}</span>
            </div>
          </div>
        </div>
        <div className="bot-history-stats">
          <div>
            <small>Elo</small>
            <strong>{bot.rating.toFixed(1)}</strong>
          </div>
          <div>
            <small>Record</small>
            <strong>
              {bot.wins}-{bot.draws}-{bot.losses}
            </strong>
          </div>
          <div>
            <small>Games</small>
            <strong>{page.total}</strong>
          </div>
        </div>
      </div>
      <div className="game-list history-list">
        {games.map((game) => (
          <Link
            className="game-row history-row"
            to={`/games/${game.id}`}
            key={game.id}
          >
            <span className="history-opponent">
              {game.opponentAvatarUrl && (
                <BotAvatar
                  src={game.opponentAvatarUrl}
                  name={game.opponentName}
                  style={game.opponentAvatarStyle}
                />
              )}
              <span>
                <strong>vs {game.opponentName}</strong>
                <small>
                  Played as {game.botColor === "white" ? "White" : "Black"} ·{" "}
                  {game.mode} · {game.timeControl} ·{" "}
                  {historyDate(game.createdAt)}
                </small>
              </span>
            </span>
            <b className={"outcome " + game.outcome}>
              {outcomeLabels[game.outcome]}
            </b>
            <span className={"live-dot " + game.status}>{game.status}</span>
          </Link>
        ))}
        {!games.length && (
          <p className="empty">{theme.copy.pages.historyEmpty}</p>
        )}
      </div>
      {error && <p className="error history-error">{error}</p>}
      {games.length < page.total && (
        <button className="load-more secondary" disabled={busy} onClick={more}>
          {busy
            ? "Loading…"
            : `Load more · ${page.total - games.length} remaining`}
        </button>
      )}
    </main>
  );
}

function formatClock(value: number | null) {
  if (value == null) return "—";
  const safe = Math.max(0, value);
  return `${Math.floor(safe / 60000)}:${Math.floor((safe % 60000) / 1000)
    .toString()
    .padStart(2, "0")}.${Math.floor((safe % 1000) / 100)}`;
}
function scoreLabel(analysis: Analysis) {
  if (!analysis) return "…";
  if (analysis.mate != null)
    return analysis.mate > 0
      ? `#${analysis.mate}`
      : `#-${Math.abs(analysis.mate)}`;
  return `${analysis.eval > 0 ? "+" : ""}${analysis.eval.toFixed(2)}`;
}
function wsAddress(path: string) {
  const configured = import.meta.env.VITE_API_URL || window.location.origin;
  const url = new URL(path, configured);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.toString();
}

function GamePage() {
  const { theme } = useTheme();
  const { id } = useParams();
  const navigate = useNavigate();
  const [game, setGame] = useState<Game>();
  const [connected, setConnected] = useState(false);
  const [selected, setSelected] = useState<number | null>(null);
  const [orientation, setOrientation] = useState<"white" | "black">("white");
  const socket = useRef<WebSocket | null>(null);
  useEffect(() => {
    if (!id) return;
    api<Game>(`/api/games/${id}`).then((g) => {
      setGame(g);
      if (g.humanColor) setOrientation(g.humanColor);
    });
    const ws = new WebSocket(wsAddress(`/api/games/${id}/stream`));
    socket.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (e) => {
      const message = JSON.parse(e.data);
      if (message.type === "snapshot") setGame(message.game);
    };
    return () => ws.close();
  }, [id]);
  const latest = (game?.moves.length || 0) - 1;
  const ply = selected == null ? latest : selected;
  const fen =
    ply < 0 ? new Chess().fen() : game?.moves[ply]?.fen || new Chess().fen();
  const analysis = game?.analysis?.[ply] || null;
  const lastMove = ply >= 0 ? game?.moves[ply]?.uci : undefined;
  useEffect(() => {
    if (selected != null && socket.current?.readyState === WebSocket.OPEN)
      socket.current.send(JSON.stringify({ type: "focus_ply", ply: selected }));
  }, [selected]);
  useEffect(() => {
    const navigateMoves = (event: KeyboardEvent) => {
      if (
        (event.key !== "ArrowLeft" && event.key !== "ArrowRight") ||
        event.altKey ||
        event.ctrlKey ||
        event.metaKey
      )
        return;
      const target = event.target as HTMLElement | null;
      if (
        target?.closest('input,select,textarea,[contenteditable="true"]') ||
        document.querySelector(".promotion")
      )
        return;
      if (event.key === "ArrowLeft") {
        if (latest < 0) return;
        event.preventDefault();
        setSelected((current) =>
          Math.max(-1, (current == null ? latest : current) - 1),
        );
        return;
      }
      setSelected((current) => {
        if (current == null) return current;
        event.preventDefault();
        return current >= latest ? null : current + 1;
      });
    };
    addEventListener("keydown", navigateMoves);
    return () => removeEventListener("keydown", navigateMoves);
  }, [latest]);
  if (!game)
    return <main className="game-loading">{theme.copy.live.thinking}</main>;
  const atLatest = ply === latest;
  const humanTurn =
    game.mode === "human" &&
    game.status === "running" &&
    atLatest &&
    game.humanColor === game.turn;
  const move = async (uci: string) => {
    try {
      setGame(
        await api(`/api/human-games/${game.id}/move`, {
          method: "POST",
          body: JSON.stringify({ uci }),
        }),
      );
    } catch (x: any) {
      alert(x.message);
    }
  };
  const evalPercent = analysis
    ? Math.max(4, Math.min(96, 50 + analysis.eval * 7))
    : 50;
  return (
    <main className="live-page route-live">
      <div className="game-top">
        <button className="ghost" onClick={() => navigate(-1)}>
          ← {theme.copy.live.back}
        </button>
        <div className={"connection " + (connected ? "online" : "offline")}>
          <i />
          {connected ? theme.copy.live.connected : theme.copy.live.reconnecting}
        </div>
        <button
          className="ghost"
          onClick={() =>
            setOrientation((o) => (o === "white" ? "black" : "white"))
          }
        >
          ⇅ {theme.copy.live.flip}
        </button>
      </div>
      <div className="live-layout">
        <section className="board-column">
          <Player
            name={orientation === "white" ? game.blackName : game.whiteName}
            avatarUrl={
              orientation === "white"
                ? game.blackAvatarUrl
                : game.whiteAvatarUrl
            }
            avatarStyle={
              orientation === "white"
                ? game.blackAvatarStyle
                : game.whiteAvatarStyle
            }
            clock={
              orientation === "white" ? game.blackClockMs : game.whiteClockMs
            }
            active={
              game.status === "running" &&
              game.turn === (orientation === "white" ? "black" : "white")
            }
          />
          <div className="board-with-eval">
            <div className="eval-bar">
              <div style={{ height: `${evalPercent}%` }} />
              <span>{scoreLabel(analysis)}</span>
            </div>
            <ArenaBoard
              fen={fen}
              orientation={orientation}
              interactive={humanTurn}
              lastMove={lastMove}
              whiteAvatarUrl={game.whiteAvatarUrl}
              blackAvatarUrl={game.blackAvatarUrl}
              whiteAvatarStyle={game.whiteAvatarStyle}
              blackAvatarStyle={game.blackAvatarStyle}
              onMove={move}
            />
          </div>
          <Player
            name={orientation === "white" ? game.whiteName : game.blackName}
            avatarUrl={
              orientation === "white"
                ? game.whiteAvatarUrl
                : game.blackAvatarUrl
            }
            avatarStyle={
              orientation === "white"
                ? game.whiteAvatarStyle
                : game.blackAvatarStyle
            }
            clock={
              orientation === "white" ? game.whiteClockMs : game.blackClockMs
            }
            active={
              game.status === "running" &&
              game.turn === (orientation === "white" ? "white" : "black")
            }
          />
        </section>
        <aside className="game-panel">
          <div className="game-title">
            <span className="eyebrow">
              {game.mode} · {game.timeControl}
            </span>
            <h2>
              {game.whiteName} <small>vs</small> {game.blackName}
            </h2>
            <p className={"game-state " + game.status}>
              {game.status === "running"
                ? "Game in progress"
                : game.status === "completed"
                  ? `${game.result} · ${game.termination || "finished"}`
                  : game.error || game.status}
            </p>
          </div>
          <div className="analysis-panel">
            <span>{theme.copy.pages.analysis}</span>
            <strong>{scoreLabel(analysis)}</strong>
            <p>
              {analysis?.pv?.length
                ? analysis.pv.join(" ")
                : connected
                  ? theme.copy.live.analyzing
                  : theme.copy.live.paused}
            </p>
            {analysis?.depth && (
              <small>Depth {analysis.depth} · White perspective</small>
            )}
          </div>
          <div className="move-sheet">
            <button
              className={ply === -1 ? "selected" : ""}
              onClick={() => setSelected(-1)}
            >
              Start
            </button>
            {game.moves.map((m, index) => (
              <button
                className={ply === index ? "selected" : ""}
                onClick={() => setSelected(index)}
                key={index}
              >
                <span>
                  {index % 2 === 0 ? `${Math.floor(index / 2) + 1}.` : "…"}
                </span>
                {m.san}
              </button>
            ))}
          </div>
          <div className="playback">
            <button
              aria-label="Previous move"
              onClick={() => setSelected(Math.max(-1, ply - 1))}
            >
              ←
            </button>
            <span>
              {ply + 1} / {game.moves.length}
              <small>← / → moves</small>
            </span>
            <button
              aria-label="Next move"
              onClick={() => setSelected(ply >= latest ? null : ply + 1)}
            >
              →
            </button>
            <button onClick={() => setSelected(null)}>Live ⏭</button>
          </div>
          {game.mode === "human" && game.status === "running" && (
            <button
              className="danger full"
              onClick={async () => {
                if (confirm("Resign this game?"))
                  setGame(
                    await api(`/api/human-games/${game.id}/resign`, {
                      method: "POST",
                    }),
                  );
              }}
            >
              {theme.copy.live.resign}
            </button>
          )}
          {game.mode !== "human" &&
            game.canAbort &&
            ["queued", "running"].includes(game.status) && (
              <button
                className="danger full"
                onClick={async () => {
                  if (confirm("Abort this showdown?"))
                    setGame(
                      await api(`/api/games/${game.id}/abort`, {
                        method: "POST",
                      }),
                    );
                }}
              >
                {theme.copy.live.abort}
              </button>
            )}
          {game.mode === "human" && game.status === "running" && !humanTurn && (
            <p className="thinking">
              {game.turn === game.humanColor
                ? "Your turn"
                : theme.copy.live.thinking}
            </p>
          )}
        </aside>
      </div>
    </main>
  );
}

function Player({
  name,
  avatarUrl,
  avatarStyle,
  clock,
  active,
}: {
  name: string;
  avatarUrl?: string;
  avatarStyle?: AvatarStyle;
  clock: number | null;
  active: boolean;
}) {
  return (
    <div className={"player " + (active ? "active" : "")}>
      {avatarUrl ? (
        <BotAvatar src={avatarUrl} name={name} style={avatarStyle} />
      ) : (
        <div className="avatar">{name[0]?.toUpperCase()}</div>
      )}
      <strong>{name}</strong>
      {clock != null && <time>{formatClock(clock)}</time>}
    </div>
  );
}

function Upload({ refresh }: { refresh: () => void }) {
  const { theme } = useTheme();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState<File>();
  const [avatar, setAvatar] = useState<File>();
  const [preview, setPreview] = useState("");
  const [message, setMessage] = useState("");
  useEffect(
    () => () => {
      if (preview) URL.revokeObjectURL(preview);
    },
    [preview],
  );
  const chooseAvatar = async (next?: File) => {
    setAvatar(undefined);
    setMessage("");
    if (!next) {
      setPreview("");
      return;
    }
    const error = await avatarError(next);
    if (error) {
      setPreview("");
      setMessage(error);
      return;
    }
    setAvatar(next);
    setPreview(URL.createObjectURL(next));
  };
  return (
    <main className="setup-shell route-upload">
      <Link className="back" to="/">
        ← {theme.copy.nav.arena}
      </Link>
      <div className="card setup-card">
        <span className="eyebrow">{theme.copy.pages.uploadEyebrow}</span>
        <h1>{theme.copy.pages.upload}</h1>
        <p>{theme.copy.pages.uploadBody}</p>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            if (!file || !avatar) return;
            const data = new FormData();
            data.append("name", name);
            data.append("description", description);
            data.append("binary", file);
            data.append("avatar", avatar);
            try {
              const result = await api("/api/bots", {
                method: "POST",
                body: data,
              });
              location.hash = `claim=${result.bot.id}:${result.recoveryToken}`;
              setMessage(
                "Uploaded. Save the recovery URL. UCI validation is running.",
              );
              setName("");
              setDescription("");
              setAvatar(undefined);
              setPreview("");
              refresh();
            } catch (x: any) {
              setMessage(x.message);
            }
          }}
        >
          <label>
            Bot name
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              maxLength={40}
            />
          </label>
          <label>
            Bot description{" "}
            <span className="field-counter">{description.length}/280</span>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              maxLength={280}
              rows={4}
              placeholder="Describe the engine's style, opening book, or battle plan…"
            />
          </label>
          <label>
            Executable · Linux x86-64 ELF, maximum 50 MB
            <input
              type="file"
              onChange={(e) => setFile(e.target.files?.[0])}
              required
            />
          </label>
          <label>
            Mask · transparent PNG, 128×128, maximum 256 KB
            <input
              type="file"
              accept="image/png"
              onChange={(e) => chooseAvatar(e.target.files?.[0])}
              required
            />
          </label>
          {preview && (
            <div className="avatar-preview">
              <img src={preview} alt="Mask preview" />
              <span>
                This mask will cover the face of every piece. Keep at least 10%
                of the canvas fully transparent.
              </span>
            </div>
          )}
          <button disabled={!avatar || !description.trim()}>
            {theme.copy.pages.uploadButton}
          </button>
          {message && (
            <p className={message.startsWith("Uploaded") ? "success" : "error"}>
              {message}
            </p>
          )}
        </form>
      </div>
    </main>
  );
}

function Admin({ refresh, bots }: { refresh: () => void; bots: Bot[] }) {
  const { theme } = useTheme();
  const [open, setOpen] = useState(false);
  const [pw, setPw] = useState("admin-fightclub");
  const [settings, setSettings] = useState<any>();
  const [run, setRun] = useState<RatingRun>();
  const [busy, setBusy] = useState("");
  const [notice, setNotice] = useState("");
  const loadRun = async () => {
    try {
      const value = await api<RatingRun>("/api/admin/rating-runs/current");
      setRun(value);
      if (value.status === "running" || value.status === "completed") refresh();
    } catch {}
  };
  useEffect(() => {
    if (!settings) return;
    loadRun();
    const timer = setInterval(loadRun, 1500);
    return () => clearInterval(timer);
  }, [Boolean(settings)]);
  const failed = (error: any) => {
    setNotice(error.message);
    setBusy("");
  };
  if (!open)
    return (
      <button className="text" onClick={() => setOpen(true)}>
        {theme.copy.nav.admin}
      </button>
    );
  if (!settings)
    return (
      <div className="admin-pop">
        <h3>{theme.copy.pages.admin}</h3>
        <input
          type="password"
          value={pw}
          onChange={(e) => setPw(e.target.value)}
        />
        <button
          onClick={async () => {
            try {
              await api("/api/auth/admin", {
                method: "POST",
                body: JSON.stringify({ password: pw }),
              });
              setSettings(await api("/api/admin/settings"));
            } catch (x: any) {
              alert(x.message);
            }
          }}
        >
          Unlock
        </button>
      </div>
    );
  const running = run?.status === "queued" || run?.status === "running";
  const progress = run?.totalGames
    ? Math.round((100 * run.completedGames) / run.totalGames)
    : 0;
  return (
    <div className="admin-pop admin-wide">
      <div className="section-head">
        <h3>{theme.copy.pages.admin}</h3>
        <button className="secondary" onClick={() => setOpen(false)}>
          Close
        </button>
      </div>
      <label>
        Games per pairing
        <input
          type="number"
          min="2"
          max="100"
          step="2"
          value={settings.gamesPerPair}
          onChange={(e) =>
            setSettings({ ...settings, gamesPerPair: +e.target.value })
          }
        />
      </label>
      <label>
        Rated time control
        <input
          value={settings.timeControl}
          onChange={(e) =>
            setSettings({ ...settings, timeControl: e.target.value })
          }
        />
      </label>
      <label>
        K-factor
        <input
          type="number"
          min="1"
          max="128"
          value={settings.kFactor}
          onChange={(e) =>
            setSettings({ ...settings, kFactor: +e.target.value })
          }
        />
      </label>
      <div className="admin-actions">
        <button
          disabled={Boolean(busy)}
          onClick={async () => {
            setBusy("save");
            setNotice("");
            try {
              await api("/api/admin/settings", {
                method: "PUT",
                body: JSON.stringify({
                  games_per_pair: settings.gamesPerPair,
                  time_control: settings.timeControl,
                  k_factor: settings.kFactor,
                }),
              });
              setNotice("Settings saved.");
              setBusy("");
            } catch (x: any) {
              failed(x);
            }
          }}
        >
          {busy === "save" ? "Saving…" : "Save settings"}
        </button>
        <button
          disabled={running || Boolean(busy)}
          className="secondary"
          onClick={async () => {
            setBusy("run");
            setNotice("");
            try {
              setRun(
                await api("/api/admin/rating-runs/missing", { method: "POST" }),
              );
              setNotice("Missing matches queued.");
              setBusy("");
            } catch (x: any) {
              failed(x);
            }
          }}
        >
          {running ? "Matches running…" : "Run missing matches"}
        </button>
        <button
          disabled={running || Boolean(busy)}
          className="secondary"
          onClick={async () => {
            setBusy("recount");
            setNotice("");
            try {
              const result = await api<any>("/api/admin/recount", {
                method: "POST",
              });
              setNotice(
                `Recalculated ${result.competitorsUpdated} competitors from ${result.gamesProcessed} games; ${result.changes.length} ratings changed.`,
              );
              refresh();
              setBusy("");
            } catch (x: any) {
              failed(x);
            }
          }}
        >
          {busy === "recount" ? "Recalculating…" : "Recalculate Elo"}
        </button>
      </div>
      {run && run.status !== "idle" && (
        <div className={"rating-run " + run.status}>
          <div>
            <strong>
              {run.status === "completed"
                ? "Rating run complete"
                : run.status === "failed"
                  ? "Rating run failed"
                  : "Rating run in progress"}
            </strong>
            <span>
              {run.completedGames}/{run.totalGames} games ·{" "}
              {run.completedPairings}/{run.totalPairings} pairings
            </span>
          </div>
          <div className="progress">
            <i style={{ width: `${progress}%` }} />
          </div>
          {run.currentPairing && <small>{run.currentPairing}</small>}
          {run.error && <small className="error">{run.error}</small>}
        </div>
      )}
      {notice && (
        <p
          className={
            notice.toLowerCase().includes("failed") ||
            notice.toLowerCase().includes("must")
              ? "error"
              : "success"
          }
        >
          {notice}
        </p>
      )}
      <h4>Competitors</h4>
      {bots.map((b) => (
        <div className="admin-row" key={b.id}>
          <BotAvatar src={b.avatarUrl} name={b.name} style={b.avatarStyle} />
          <span>
            {b.name}
            {b.system ? " · benchmark" : ""} · {b.rating}
          </span>
          {!b.system && (
            <button
              className="secondary"
              onClick={async () => {
                const description = prompt(
                  "Bot description (max 280 characters)",
                  b.description || "",
                );
                if (description === null) return;
                try {
                  await api(`/api/bots/${b.id}`, {
                    method: "PATCH",
                    body: JSON.stringify({ description }),
                  });
                  refresh();
                  setNotice(`${b.name} description updated.`);
                } catch (x: any) {
                  failed(x);
                }
              }}
            >
              Bio
            </button>
          )}
          <button
            className="secondary"
            onClick={async () => {
              const value = prompt("Set Elo", String(b.rating));
              if (value) {
                try {
                  await api(`/api/admin/bots/${b.id}/rating`, {
                    method: "POST",
                    body: JSON.stringify({
                      value: +value,
                      reason: "Admin adjustment",
                    }),
                  });
                  refresh();
                  setNotice(`${b.name} Elo updated.`);
                } catch (x: any) {
                  failed(x);
                }
              }
            }}
          >
            Set Elo
          </button>
        </div>
      ))}
    </div>
  );
}

function AuthenticatedApp() {
  const { theme } = useTheme();
  const [bots, setBots] = useState<Bot[]>([]);
  const load = () => api<Bot[]>("/api/bots").then(setBots);
  useEffect(() => {
    load();
    const timer = setInterval(load, 4000);
    const hash = location.hash.match(/claim=(\d+):(.+)/);
    if (hash)
      api(`/api/bots/${hash[1]}/claim`, {
        method: "POST",
        body: JSON.stringify({ password: hash[2] }),
      }).then(() => {
        history.replaceState(null, "", location.pathname);
        load();
      });
    return () => clearInterval(timer);
  }, []);
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/games/:id" element={<GamePage />} />
        <Route
          path="*"
          element={
            <>
              <Header bots={bots} refresh={load} />
              <Routes>
                <Route
                  path="/"
                  element={<Dashboard bots={bots} refresh={load} />}
                />
                <Route path="/games" element={<GamesList />} />
                <Route path="/bots/:id" element={<BotHistory />} />
                <Route
                  path="/showdown"
                  element={<ShowdownSetup bots={bots} />}
                />
                <Route path="/play" element={<HumanSetup bots={bots} />} />
                <Route path="/upload" element={<Upload refresh={load} />} />
                <Route path="/rules" element={<RulesPage />} />
                <Route path="*" element={<Navigate to="/" />} />
              </Routes>
              <footer>{theme.copy.footer}</footer>
            </>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default function App() {
  const { theme } = useTheme();
  const [logged, setLogged] = useState<boolean>();
  const [effects, setEffects] = useState<EffectMode>(savedEffects);
  const [appearanceOpen, setAppearanceOpen] = useState(effects === "unset");
  const [firstRun, setFirstRun] = useState(effects === "unset");
  useEffect(() => {
    api("/api/auth/session")
      .then(() => setLogged(true))
      .catch(() => setLogged(false));
  }, []);
  useEffect(() => {
    document.documentElement.dataset.effects =
      effects === "full" ? "full" : "static";
  }, [effects]);
  const choose = (mode: "full" | "static") => {
    localStorage.setItem(EFFECTS_KEY, mode);
    setEffects(mode);
  };
  if (logged === undefined) return null;
  return (
    <>
      <ThemeDecor />
      {logged ? <AuthenticatedApp /> : <Login done={() => setLogged(true)} />}
      <button
        className="effects-fab"
        aria-label="Change DeathPit appearance"
        title="Change DeathPit appearance"
        onClick={() => setAppearanceOpen(true)}
      >
        {theme.symbol} <span>LOOK</span>
      </button>
      <AppearanceMenu
        open={appearanceOpen}
        firstRun={firstRun}
        effects={effects}
        onEffects={choose}
        onClose={() => {
          setAppearanceOpen(false);
          setFirstRun(false);
        }}
      />
    </>
  );
}
