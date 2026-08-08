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
  "everforest",
  "tokyonight",
  "gruvbox",
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
            "Feed the pit a Linux x86-64 ELF UCI engine and optionally forge it a transparent battle mask.",
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
            "Upload a Linux UCI engine, optionally give it a face, and let it disappoint you beautifully.",
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
            "Bring a Linux UCI engine, name it, and optionally mask it before putting it on the block.",
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
            "Upload a Linux x86-64 UCI binary, document it, and optionally assign a transparent process mask.",
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
            "Present a Linux UCI engine, its testimony, and an optional transparent ceremonial mask.",
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
            "Bring a Linux UCI engine, describe its style, and optionally give it a transparent mask.",
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
  everforest: {
    id: "everforest",
    label: "Everforest",
    symbol: "✿",
    description: "Moss, wildflowers, warm wood, and a meadow-bound Reaper.",
    board: {
      light: "#d3c6aa",
      dark: "#47584d",
      selected: "#a7c080",
      legal: "rgba(131,160,106,.62)",
      lastFrom: "rgba(127,187,179,.48)",
      lastTo: "rgba(167,192,128,.68)",
      border: "#7fbbb3",
      shadow: "rgba(35,48,42,.68)",
    },
    copy: common(
      {
        tagline: "Let the wild think. Let the board grow.",
        nav: {
          arena: "Grove",
          games: "Rings",
          upload: "Plant",
          rules: "Field Notes",
          admin: "Gardener",
        },
        login: {
          eyebrow: "PRIVATE EVERGREEN GROVE",
          body: "Bring an engine into the clearing and see which line finds the light.",
          password: "Grove password",
          enter: "Enter the grove",
        },
        rules: {
          eyebrow: "THE GARDEN CODEX",
          title: "Field Notes",
          footer: "Keep the grove private. Let every move take root.",
        },
        ladder: {
          eyebrow: "RING COUNT",
          title: "Forest Standings",
          hide: "Hide the saplings",
          show: "Show the saplings",
          empty: "No new growth has reached the clearing.",
        },
        actions: {
          showdown: {
            eyebrow: "TREE VS TREE",
            title: "Watch the canopy",
            body: "Two engines trade branches beneath a patient green sky.",
            cta: "Open the clearing →",
          },
          play: {
            eyebrow: "YOU VS THE WILDERNESS",
            title: "Play among the roots",
            body: "Choose a side, set the pace, and find the quiet path forward.",
            cta: "Walk to the board →",
          },
        },
        pages: {
          showdown: "Canopy duel",
          showdownEyebrow: "LIVE IN THE CLEARING",
          showdownBody: "The grove slows the branches so every witness can follow.",
          startShowdown: "Start the duel",
          play: "Your forest game",
          playEyebrow: "FOLLOW THE ROOTS",
          startPlay: "Take a step",
          games: "Tree rings",
          gamesEyebrow: "ARCHIVE OF GROWTH",
          gamesEmpty: "The rings are still unmarked.",
          history: "Rings of",
          historyEmpty: "This tree has no recorded seasons yet.",
          upload: "Plant a challenger",
          uploadEyebrow: "A NEW SEEDLING",
          uploadBody: "Bring a Linux UCI engine, describe its nature, and optionally give it a transparent woodland mask.",
          uploadButton: "Plant in the grove",
          admin: "Garden shed",
          analysis: "ROOT SYSTEM ANALYSIS",
        },
        live: {
          back: "Back to the grove",
          connected: "Grove connection",
          reconnecting: "Finding the trail…",
          flip: "Turn the board",
          analyzing: "Reading the rings…",
          paused: "The grove is waiting for the signal",
          live: "Live in the canopy",
          resign: "Return to the path",
          abort: "Close the clearing",
          thinking: "The engine is listening…",
        },
        footer: "ChESSPIT · let the wild think",
      },
      "Mossy greens, wildflowers, warm timber, and a flower-crowned Grim Reaper in the deep grove.",
    ),
  },
  tokyonight: {
    id: "tokyonight",
    label: "Tokyo Night",
    symbol: "◈",
    description: "Neon rain, indigo streets, cyan circuits, and a cyber Reaper.",
    board: {
      light: "#a9b1d6",
      dark: "#292e42",
      selected: "#7aa2f7",
      legal: "rgba(125,207,255,.58)",
      lastFrom: "rgba(187,154,247,.5)",
      lastTo: "rgba(125,207,255,.68)",
      border: "#bb9af7",
      shadow: "rgba(8,10,24,.86)",
    },
    copy: common(
      {
        tagline: "Neon wakes. Engines calculate. The city watches.",
        nav: {
          arena: "District",
          games: "Runs",
          upload: "Jack In",
          rules: "Protocol",
          admin: "Operator",
        },
        login: {
          eyebrow: "PRIVATE NIGHT GRID",
          body: "Connect a UCI engine to the midnight network and let its line glow under pressure.",
          password: "Grid access key",
          enter: "Enter the night",
        },
        rules: {
          eyebrow: "NIGHT PROTOCOL",
          title: "Protocol",
          footer: "Keep the grid private. Let the signal reveal the move.",
        },
        ladder: {
          eyebrow: "LIVE TELEMETRY",
          title: "Signal Rankings",
          hide: "Hide baseline signals",
          show: "Show baseline signals",
          empty: "No new signals are broadcasting.",
        },
        actions: {
          showdown: {
            eyebrow: "PROCESS VS PROCESS",
            title: "Watch the neon duel",
            body: "Two engines collide in a rain-slick district of live clocks and bright lines.",
            cta: "Open the district →",
          },
          play: {
            eyebrow: "PILOT VS MACHINE",
            title: "Enter the signal",
            body: "Pick your color, tune the timer, and make one clean move through the noise.",
            cta: "Jack into the board →",
          },
        },
        pages: {
          showdown: "Neon duel",
          showdownEyebrow: "LIVE ON THE NIGHT GRID",
          showdownBody: "The feed gives every move enough space to read through the rain.",
          startShowdown: "Launch the duel",
          play: "Your night run",
          playEyebrow: "PILOT THE LINE",
          startPlay: "Start the run",
          games: "Replay cache",
          gamesEyebrow: "ARCHIVED SIGNALS",
          gamesEmpty: "The cache is empty. No signal has survived yet.",
          history: "Run log for",
          historyEmpty: "This process has no logged runs.",
          upload: "Upload a process",
          uploadEyebrow: "NEW SIGNAL DETECTED",
          uploadBody: "Upload a Linux UCI engine, give it a callsign, and optionally assign a transparent neon mask.",
          uploadButton: "Connect to the grid",
          admin: "Operator console",
          analysis: "NEURAL TELEMETRY",
        },
        live: {
          back: "Back to district",
          connected: "Signal locked",
          reconnecting: "Reacquiring the grid…",
          flip: "Flip the viewport",
          analyzing: "Tracing the brightest line…",
          paused: "The feed is dark",
          live: "Live signal",
          resign: "Disconnect",
          abort: "Terminate the run",
          thinking: "The process is calculating…",
        },
        footer: "ChESSPIT · neon wakes · engines calculate",
      },
      "Electric indigo nights, holographic rain, glowing signage, and a cybernetic Grim Reaper.",
    ),
  },
  gruvbox: {
    id: "gruvbox",
    label: "Gruvbox",
    symbol: "☼",
    description: "Warm paper, autumn leaves, old woodcuts, and a roadside Reaper.",
    board: {
      light: "#d5c4a1",
      dark: "#504945",
      selected: "#fabd2f",
      legal: "rgba(184,187,38,.62)",
      lastFrom: "rgba(254,128,25,.46)",
      lastTo: "rgba(250,189,47,.68)",
      border: "#d79921",
      shadow: "rgba(29,24,20,.78)",
    },
    copy: common(
      {
        tagline: "Warm pixels. Sharp tactics. No blue light.",
        nav: {
          arena: "Workshop",
          games: "Games",
          upload: "Forge",
          rules: "Manual",
          admin: "Foreman",
        },
        login: {
          eyebrow: "PRIVATE WOODSHOP",
          body: "Bring a UCI engine to the workbench and see which hand-carved line holds under pressure.",
          password: "Workshop key",
          enter: "Open the workshop",
        },
        rules: {
          eyebrow: "THE OLD MANUAL",
          title: "Workshop Rules",
          footer: "Keep the workshop private. Make every move count.",
        },
        ladder: {
          eyebrow: "BENCHMARK BOARD",
          title: "Workshop Standings",
          hide: "Hide the house tools",
          show: "Show the house tools",
          empty: "No new tools are on the bench.",
        },
        actions: {
          showdown: {
            eyebrow: "TOOL VS TOOL",
            title: "Watch the carving",
            body: "Two engines work the same position with clocks, grit, and a little sawdust.",
            cta: "Start the work →",
          },
          play: {
            eyebrow: "PLAYER VS MACHINE",
            title: "Take the workbench",
            body: "Choose a side, set the pace, and carve a line worth keeping.",
            cta: "Sit at the board →",
          },
        },
        pages: {
          showdown: "Workshop match",
          showdownEyebrow: "LIVE FROM THE BENCH",
          showdownBody: "The work is paced so every tactic can be inspected before the next cut.",
          startShowdown: "Start the match",
          play: "Your workbench",
          playEyebrow: "MAKE YOUR CUT",
          startPlay: "Begin the work",
          games: "Old ledgers",
          gamesEyebrow: "ARCHIVE OF MATCHES",
          gamesEmpty: "The ledger has no entries yet.",
          history: "Ledger of",
          historyEmpty: "This tool has no recorded work.",
          upload: "Forge a challenger",
          uploadEyebrow: "NEW TOOL ON THE BENCH",
          uploadBody: "Upload a Linux UCI engine, describe its character, and optionally give it a transparent woodcut mask.",
          uploadButton: "Put it on the bench",
          admin: "Foreman desk",
          analysis: "TACTICAL WORKBENCH",
        },
        live: {
          back: "Back to the bench",
          connected: "Workbench linked",
          reconnecting: "Reconnecting the wire…",
          flip: "Turn the board",
          analyzing: "Inspecting the cut…",
          paused: "The bench is waiting",
          live: "Live work",
          resign: "Set down the tool",
          abort: "Close the ledger",
          thinking: "The engine is measuring twice…",
        },
        footer: "ChESSPIT · warm pixels · sharp tactics",
      },
      "A warm terminal woodcut: paper cream, rust orange, mustard gold, olive leaves, and old workshop grit.",
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
