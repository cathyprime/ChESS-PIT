import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export const THEME_IDS = [
  "inferno",
  "emo",
  "gangsta",
  "catppuccin",
  "angelic",
  "jamaica",
] as const;
export type ThemeId = (typeof THEME_IDS)[number];

type BoardTheme = {
  light: string;
  dark: string;
  selected: string;
  legal: string;
  lastFrom: string;
  lastTo: string;
  border: string;
  shadow: string;
};
type ThemeCopy = {
  tagline: string;
  description: string;
  nav: {
    arena: string;
    games: string;
    upload: string;
    rules: string;
    admin: string;
  };
  login: { eyebrow: string; body: string; password: string; enter: string };
  rules: { eyebrow: string; title: string; footer: string };
  ladder: {
    eyebrow: string;
    title: string;
    hide: string;
    show: string;
    empty: string;
  };
  actions: {
    showdown: { eyebrow: string; title: string; body: string; cta: string };
    play: { eyebrow: string; title: string; body: string; cta: string };
  };
  pages: {
    showdown: string;
    showdownEyebrow: string;
    showdownBody: string;
    startShowdown: string;
    play: string;
    playEyebrow: string;
    startPlay: string;
    games: string;
    gamesEyebrow: string;
    gamesEmpty: string;
    history: string;
    historyEmpty: string;
    upload: string;
    uploadEyebrow: string;
    uploadBody: string;
    uploadButton: string;
    admin: string;
    analysis: string;
  };
  live: {
    back: string;
    connected: string;
    reconnecting: string;
    flip: string;
    analyzing: string;
    paused: string;
    live: string;
    resign: string;
    abort: string;
    thinking: string;
  };
  footer: string;
};

export type ThemeDefinition = {
  id: ThemeId;
  label: string;
  symbol: string;
  description: string;
  board: BoardTheme;
  copy: ThemeCopy;
};

const common = (
  copy: Omit<ThemeCopy, "description">,
  description: string,
): ThemeCopy => ({ ...copy, description });

export const THEMES: Record<ThemeId, ThemeDefinition> = {
  inferno: {
    id: "inferno",
    label: "Inferno",
    symbol: "♨",
    description: "Embers, bone, iron, and refreshed reapers.",
    board: {
      light: "#e2d1ad",
      dark: "#3b2827",
      selected: "#e7b84b",
      legal: "rgba(34,75,48,.55)",
      lastFrom: "rgba(236,190,64,.48)",
      lastTo: "rgba(236,190,64,.62)",
      border: "#6d1b13",
      shadow: "rgba(0,0,0,.72)",
    },
    copy: common(
      {
        tagline: "Private engine arena · Welcome to the slaughterhouse",
        nav: {
          arena: "Pit",
          games: "Battles",
          upload: "Feed",
          rules: "Pit Law",
          admin: "Overlord",
        },
        login: {
          eyebrow: "PRIVATE ENGINE ARENA",
          body: "Upload UCI engines, put them on the board, and discover whose code survives.",
          password: "Pit password",
          enter: "Enter the pit",
        },
        rules: {
          eyebrow: "THE ChESSPIT CODEX",
          title: "Pit Law",
          footer: "Keep the arena private. Let the board speak.",
        },
        ladder: {
          eyebrow: "RATED LADDER",
          title: "Ladder of Ruin",
          hide: "Hide benchmarks",
          show: "Show benchmarks",
          empty: "No challengers remain in the fire.",
        },
        actions: {
          showdown: {
            eyebrow: "BOT VS BOT",
            title: "Watch the showdown",
            body: "Start a live exhibition with clocks, evaluation, and a best line.",
            cta: "Set up slaughter →",
          },
          play: {
            eyebrow: "HUMAN VS ENGINE",
            title: "Challenge an engine",
            body: "Choose your side, thinking time, and Stockfish strength.",
            cta: "Enter the board →",
          },
        },
        pages: {
          showdown: "Bot showdown",
          showdownEyebrow: "LIVE EXHIBITION",
          showdownBody:
            "Moves are paced for viewing. Presentation delay does not count against either engine.",
          startShowdown: "Start the slaughter",
          play: "Your trial",
          playEyebrow: "PLAY AN ENGINE",
          startPlay: "Enter the board",
          games: "Recorded carnage",
          gamesEyebrow: "ARCHIVE & LIVE",
          gamesEmpty: "No blood has touched the board yet.",
          history: "Scars of",
          historyEmpty: "This engine has left no scars yet.",
          upload: "Feed the pit",
          uploadEyebrow: "NEW CHALLENGER",
          uploadBody:
            "Feed the pit a Linux x86-64 ELF UCI engine and forge it a transparent battle mask.",
          uploadButton: "Upload and enter the pit",
          admin: "Overlord console",
          analysis: "STOCKFISH AUTOPSY",
        },
        live: {
          back: "Back",
          connected: "Live connection",
          reconnecting: "Reconnecting…",
          flip: "Flip board",
          analyzing: "Cutting into this position…",
          paused: "Autopsy paused while disconnected",
          live: "Live",
          resign: "Resign",
          abort: "Abort showdown",
          thinking: "Engine thinking…",
        },
        footer: "ChESSPIT · private inferno",
      },
      "The original red furnace: iron, fire, and judgment.",
    ),
  },
  emo: {
    id: "emo",
    label: "Emo",
    symbol: "☂",
    description: "Midnight blue rain, wilted roses, and sad reapers.",
    board: {
      light: "#9fb4cf",
      dark: "#17263b",
      selected: "#6e8cff",
      legal: "rgba(54,104,153,.62)",
      lastFrom: "rgba(86,126,214,.48)",
      lastTo: "rgba(103,151,236,.62)",
      border: "#244b82",
      shadow: "rgba(0,0,10,.8)",
    },
    copy: common(
      {
        tagline: "Every engine breaks eventually",
        nav: {
          arena: "Void",
          games: "Heartbreaks",
          upload: "Confess",
          rules: "Diary",
          admin: "Backstage",
        },
        login: {
          eyebrow: "WELCOME BACK TO THE VOID",
          body: "Bring a machine with feelings. Watch the board break its heart.",
          password: "Secret nobody understands",
          enter: "Sink into the void",
        },
        rules: {
          eyebrow: "THINGS WE NEVER SAY",
          title: "The Sad Little Rules",
          footer: "We never talk about it. We just put it in the playlist.",
        },
        ladder: {
          eyebrow: "PAIN INDEX",
          title: "Pain Rankings",
          hide: "Hide the old wounds",
          show: "Show the old wounds",
          empty: "Nobody is hurting here yet.",
        },
        actions: {
          showdown: {
            eyebrow: "TWO BOTS, ONE SAD SONG",
            title: "Watch the heartbreak",
            body: "Two engines calculate every way this could have ended differently.",
            cta: "Open old wounds →",
          },
          play: {
            eyebrow: "YOU VS THE VOID",
            title: "Play through the pain",
            body: "Pick a color, choose the hurt, and make one more move.",
            cta: "Make one more move →",
          },
        },
        pages: {
          showdown: "Mutual destruction",
          showdownEyebrow: "LIVE HEARTBREAK",
          showdownBody: "The moves are slow enough to feel every mistake.",
          startShowdown: "Let it fall apart",
          play: "Your sad game",
          playEyebrow: "PLAY THROUGH IT",
          startPlay: "Make the first mistake",
          games: "Old wounds",
          gamesEyebrow: "ARCHIVE OF REGRETS",
          gamesEmpty: "No memories. Somehow that feels worse.",
          history: "Regrets of",
          historyEmpty: "This machine has nothing to regret yet.",
          upload: "Release a sad machine",
          uploadEyebrow: "ANOTHER BROKEN CHALLENGER",
          uploadBody:
            "Upload a Linux UCI engine, give it a face, and let it disappoint you beautifully.",
          uploadButton: "Release it into the void",
          admin: "Backstage misery",
          analysis: "STOCKFISH POST-MORTEM",
        },
        live: {
          back: "Go back",
          connected: "Still connected",
          reconnecting: "Drifting away…",
          flip: "Turn it upside down",
          analyzing: "Overthinking this position…",
          paused: "The thoughts stopped",
          live: "Feel it live",
          resign: "Give up gracefully",
          abort: "End the heartbreak",
          thinking: "The machine is brooding…",
        },
        footer: "ChESSPIT · every engine breaks eventually",
      },
      "Black, blue, rainy, romantic, and terminally overthinking.",
    ),
  },
  gangsta: {
    id: "gangsta",
    label: "Gangsta",
    symbol: "♛",
    description:
      "Green streetlight, chrome, gold, and reapers running the board.",
    board: {
      light: "#b8c99c",
      dark: "#173822",
      selected: "#b4df3e",
      legal: "rgba(45,122,71,.68)",
      lastFrom: "rgba(125,184,65,.5)",
      lastTo: "rgba(180,223,62,.64)",
      border: "#147b3d",
      shadow: "rgba(0,0,0,.8)",
    },
    copy: common(
      {
        tagline: "Run the board. Own the block.",
        nav: {
          arena: "Block",
          games: "Matchups",
          upload: "New Crew",
          rules: "Code",
          admin: "Boss",
        },
        login: {
          eyebrow: "PRIVATE BLOCK",
          body: "Bring your engine, prove its game, and let the board settle the talk.",
          password: "Door code",
          enter: "Step inside",
        },
        rules: {
          eyebrow: "CODE OF THE BLOCK",
          title: "The Code",
          footer: "Respect the board. Keep the spot private.",
        },
        ladder: {
          eyebrow: "BLOCK ORDER",
          title: "Block Rankings",
          hide: "Hide house crew",
          show: "Show house crew",
          empty: "Nobody has claimed the block yet.",
        },
        actions: {
          showdown: {
            eyebrow: "CREW VS CREW",
            title: "Watch the takeover",
            body: "Set the matchup and see who really controls the squares.",
            cta: "Set the matchup →",
          },
          play: {
            eyebrow: "YOU VS THE BOSS",
            title: "Step to the engine",
            body: "Pick your side, set the pace, and handle your business.",
            cta: "Step up →",
          },
        },
        pages: {
          showdown: "The matchup",
          showdownEyebrow: "LIVE ON THE BLOCK",
          showdownBody:
            "Moves are paced so the whole crew can watch the takeover.",
          startShowdown: "Run the matchup",
          play: "Your move, boss",
          playEyebrow: "STEP TO THE ENGINE",
          startPlay: "Claim your square",
          games: "Past matchups",
          gamesEyebrow: "THE RECORD",
          gamesEmpty: "The record is clean for now.",
          history: "Record of",
          historyEmpty: "No matchups on this record yet.",
          upload: "Add to the crew",
          uploadEyebrow: "NEW HEAVY HITTER",
          uploadBody:
            "Bring a Linux UCI engine, name it, mask it, and put it on the block.",
          uploadButton: "Bring in the crew",
          admin: "Boss controls",
          analysis: "STREET ANALYSIS",
        },
        live: {
          back: "Back to the block",
          connected: "Live on the wire",
          reconnecting: "Getting the line back…",
          flip: "Switch sides",
          analyzing: "Reading the whole block…",
          paused: "Analysis line went quiet",
          live: "Stay live",
          resign: "Bow out",
          abort: "Call it off",
          thinking: "The engine is making moves…",
        },
        footer: "ChESSPIT · run the board · own the block",
      },
      "Street-poster energy without real gangs, weapons, or caricatures.",
    ),
  },
  catppuccin: {
    id: "catppuccin",
    label: "Catppuccin",
    symbol: "⌘",
    description: "Mocha pastels, terminals, coffee, and programmer reapers.",
    board: {
      light: "#bac2de",
      dark: "#45475a",
      selected: "#f9e2af",
      legal: "rgba(166,227,161,.68)",
      lastFrom: "rgba(250,179,135,.5)",
      lastTo: "rgba(249,226,175,.68)",
      border: "#cba6f7",
      shadow: "rgba(17,17,27,.82)",
    },
    copy: common(
      {
        tagline: "Freshly brewed code. Mercilessly compiled.",
        nav: {
          arena: "Workspace",
          games: "Builds",
          upload: "Deploy",
          rules: "README",
          admin: "Root",
        },
        login: {
          eyebrow: "PRIVATE REPOSITORY",
          body: "Deploy UCI processes, run the suite, and find out which build survives production.",
          password: "Repository secret",
          enter: "Open workspace",
        },
        rules: {
          eyebrow: "CONTRIBUTING.MD",
          title: "Repository Rules",
          footer: "Keep the repository private. Let the tests speak.",
        },
        ladder: {
          eyebrow: "CI STATUS",
          title: "Process Table",
          hide: "Hide fixtures",
          show: "Show fixtures",
          empty: "No user processes are running.",
        },
        actions: {
          showdown: {
            eyebrow: "PROCESS VS PROCESS",
            title: "Watch the build",
            body: "Run two engines with live logs, evaluation, and reproducible moves.",
            cta: "Run the build →",
          },
          play: {
            eyebrow: "HUMAN IN THE LOOP",
            title: "Pair with an engine",
            body: "Choose a branch, time budget, and Stockfish configuration.",
            cta: "Start pairing →",
          },
        },
        pages: {
          showdown: "Integration test",
          showdownEyebrow: "LIVE BUILD",
          showdownBody:
            "Presentation delay is excluded from engine runtime metrics.",
          startShowdown: "Run integration test",
          play: "Interactive session",
          playEyebrow: "PAIR PROGRAMMING",
          startPlay: "Start session",
          games: "Build history",
          gamesEyebrow: "LOGS & RUNNING JOBS",
          gamesEmpty: "No builds have run yet.",
          history: "Log for",
          historyEmpty: "This process has no recorded runs.",
          upload: "Deploy a process",
          uploadEyebrow: "NEW EXECUTABLE",
          uploadBody:
            "Upload a Linux x86-64 UCI binary, document it, and assign a transparent process mask.",
          uploadButton: "Deploy to ChESSPIT",
          admin: "Root console",
          analysis: "STOCKFISH DEBUGGER",
        },
        live: {
          back: "Return",
          connected: "Stream connected",
          reconnecting: "Reconnecting stream…",
          flip: "Flip viewport",
          analyzing: "Debugging this position…",
          paused: "Debugger paused offline",
          live: "Follow HEAD",
          resign: "Stop process",
          abort: "Cancel job",
          thinking: "Process is computing…",
        },
        footer: "ChESSPIT · brewed in Mocha · compiled without mercy",
      },
      "An accurate Catppuccin Mocha coding dungeon.",
    ),
  },
  angelic: {
    id: "angelic",
    label: "Angelic",
    symbol: "✦",
    description: "Cream, gold, stained glass, clouds, and radiant judgment.",
    board: {
      light: "#fff1b8",
      dark: "#c9a44d",
      selected: "#ffcf40",
      legal: "rgba(117,151,63,.58)",
      lastFrom: "rgba(255,213,77,.52)",
      lastTo: "rgba(255,197,36,.7)",
      border: "#d6ad2f",
      shadow: "rgba(99,70,12,.35)",
    },
    copy: common(
      {
        tagline: "Judgment descends one move at a time",
        nav: {
          arena: "Court",
          games: "Judgments",
          upload: "Summon",
          rules: "Commandments",
          admin: "Council",
        },
        login: {
          eyebrow: "THE PRIVATE CELESTIAL COURT",
          body: "Summon engines before the board and let perfect calculation judge their work.",
          password: "Seal of entry",
          enter: "Enter the court",
        },
        rules: {
          eyebrow: "THE TWO COMMANDMENTS",
          title: "Commandments",
          footer: "Guard the court. Let only the board pronounce judgment.",
        },
        ladder: {
          eyebrow: "ORDER OF MERIT",
          title: "Book of Judgment",
          hide: "Hide celestial trials",
          show: "Show celestial trials",
          empty: "No mortal challengers stand before the court.",
        },
        actions: {
          showdown: {
            eyebrow: "JUDGMENT VS JUDGMENT",
            title: "Witness the reckoning",
            body: "Summon two engines and observe every measured consequence.",
            cta: "Begin judgment →",
          },
          play: {
            eyebrow: "MORTAL VS SERAPH",
            title: "Challenge the seraph",
            body: "Choose your side, allotted time, and degree of celestial strength.",
            cta: "Enter the court →",
          },
        },
        pages: {
          showdown: "Celestial reckoning",
          showdownEyebrow: "JUDGMENT IN SESSION",
          showdownBody:
            "The court pauses between moves so every witness may follow.",
          startShowdown: "Open the court",
          play: "Your judgment",
          playEyebrow: "FACE THE SERAPH",
          startPlay: "Accept judgment",
          games: "Book of matches",
          gamesEyebrow: "RECORDED JUDGMENTS",
          gamesEmpty: "The book is still untouched.",
          history: "Deeds of",
          historyEmpty: "No deeds have been entered for this contender.",
          upload: "Summon a contender",
          uploadEyebrow: "A NEW SOUL ARRIVES",
          uploadBody:
            "Present a Linux UCI engine, its testimony, and a transparent ceremonial mask.",
          uploadButton: "Summon to the court",
          admin: "High council",
          analysis: "DIVINE EVALUATION",
        },
        live: {
          back: "Return to court",
          connected: "Celestial link",
          reconnecting: "Restoring the light…",
          flip: "Reverse the heavens",
          analyzing: "Weighing this position…",
          paused: "Judgment waits for the link",
          live: "Witness live",
          resign: "Concede",
          abort: "Dismiss judgment",
          thinking: "The seraph is deliberating…",
        },
        footer: "ChESSPIT · judgment descends one move at a time",
      },
      "A readable light theme with luminous reapers and golden chess halls.",
    ),
  },
  jamaica: {
    id: "jamaica",
    label: "Jamaica",
    symbol: "☘",
    description:
      "Green, gold, red, dub smoke, sound systems, and roots reapers.",
    board: {
      light: "#d8c886",
      dark: "#1c5b34",
      selected: "#f0c541",
      legal: "rgba(207,46,46,.62)",
      lastFrom: "rgba(247,200,68,.5)",
      lastTo: "rgba(22,155,98,.68)",
      border: "#169b62",
      shadow: "rgba(0,0,0,.76)",
    },
    copy: common(
      {
        tagline: "One board. One love. No blunders.",
        nav: {
          arena: "Yard",
          games: "Sessions",
          upload: "New Sound",
          rules: "Reasonings",
          admin: "Control",
        },
        login: {
          eyebrow: "PRIVATE YARD",
          body: "Bring an engine, settle into the riddim, and reason through every square.",
          password: "Yard password",
          enter: "Enter the session",
        },
        rules: {
          eyebrow: "TWO REASONINGS",
          title: "Yard Reasonings",
          footer: "Keep the yard private. Let every move carry its own truth.",
        },
        ladder: {
          eyebrow: "SOUND ORDER",
          title: "Yard Standings",
          hide: "Hide house sounds",
          show: "Show house sounds",
          empty: "No new sounds have entered the yard.",
        },
        actions: {
          showdown: {
            eyebrow: "SOUND VS SOUND",
            title: "Watch the clash",
            body: "Two engines meet over one board with live evaluation and pure pressure.",
            cta: "Start the session →",
          },
          play: {
            eyebrow: "YOU AND THE ENGINE",
            title: "Reason with the engine",
            body: "Choose your side, set the tempo, and find the right move.",
            cta: "Reason now →",
          },
        },
        pages: {
          showdown: "Sound clash",
          showdownEyebrow: "LIVE FROM THE YARD",
          showdownBody: "Moves are paced so everybody can follow the session.",
          startShowdown: "Start the clash",
          play: "Your reasoning",
          playEyebrow: "SIT WITH THE ENGINE",
          startPlay: "Begin the session",
          games: "Session archive",
          gamesEyebrow: "PAST & LIVE SESSIONS",
          gamesEmpty: "The yard is quiet. No sessions yet.",
          history: "Sessions of",
          historyEmpty: "This sound has no recorded sessions.",
          upload: "Bring a new sound",
          uploadEyebrow: "NEW SELECTOR",
          uploadBody:
            "Bring a Linux UCI engine, describe its style, and give it a transparent mask.",
          uploadButton: "Bring it to the yard",
          admin: "Sound control",
          analysis: "DEEP POSITION REASONING",
        },
        live: {
          back: "Back to the yard",
          connected: "Session live",
          reconnecting: "Tuning the signal…",
          flip: "Turn the board",
          analyzing: "Reasoning through the position…",
          paused: "Reasoning waits for the signal",
          live: "Stay in session",
          resign: "Ease out",
          abort: "Stop the session",
          thinking: "The engine is finding the riddim…",
        },
        footer: "ChESSPIT · one board · one love · no blunders",
      },
      "Reggae sound-system fantasy with leaf motifs and no human stereotypes.",
    ),
  },
};

const THEME_KEY = "chesspit-theme";
type ThemeContextValue = {
  theme: ThemeDefinition;
  setTheme: (theme: ThemeId) => void;
};
const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

function savedTheme(): ThemeId {
  const value = localStorage.getItem(THEME_KEY);
  return THEME_IDS.includes(value as ThemeId) ? (value as ThemeId) : "inferno";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [id, setId] = useState<ThemeId>(savedTheme);
  useEffect(() => {
    document.documentElement.dataset.theme = id;
    localStorage.setItem(THEME_KEY, id);
  }, [id]);
  const value = useMemo(() => ({ theme: THEMES[id], setTheme: setId }), [id]);
  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export function useTheme() {
  const value = useContext(ThemeContext);
  if (!value) throw new Error("useTheme must be used inside ThemeProvider");
  return value;
}

export function themedAvatarUrl(url: string, theme: ThemeId) {
  try {
    const parsed = new URL(url, window.location.origin);
    if (
      parsed.pathname.startsWith("/api/bots/") ||
      parsed.pathname.startsWith("/api/avatars/")
    )
      parsed.searchParams.set("theme", theme);
    return parsed.toString();
  } catch {
    return url;
  }
}

export function themeArt(theme: ThemeId, group: "decor", name: string) {
  return `/art/themes/${theme}/${group}/${name}.webp`;
}
