import { useMemo, useState } from "react";
import { Chess } from "chess.js";
import {
  Chessboard,
  defaultPieces,
  type ChessboardOptions,
  type PieceRenderObject,
} from "react-chessboard";
import { assetUrl } from "./api";
import type { AvatarStyle } from "./types";
import { themedAvatarUrl, useTheme } from "./theme";

type Props = {
  fen: string;
  orientation: "white" | "black";
  interactive?: boolean;
  lastMove?: string;
  whiteAvatarUrl?: string;
  blackAvatarUrl?: string;
  whiteAvatarStyle?: AvatarStyle;
  blackAvatarStyle?: AvatarStyle;
  onMove?: (uci: string) => void;
};

export function ArenaBoard({
  fen,
  orientation,
  interactive = false,
  lastMove,
  whiteAvatarUrl,
  blackAvatarUrl,
  whiteAvatarStyle = "mask",
  blackAvatarStyle = "mask",
  onMove,
}: Props) {
  const { theme } = useTheme();
  const [selected, setSelected] = useState<string>();
  const [promotion, setPromotion] = useState<{ from: string; to: string }>();
  const chess = useMemo(() => new Chess(fen), [fen]);
  const destinations = selected
    ? chess
        .moves({ square: selected as any, verbose: true })
        .map((move) => move.to)
    : [];
  const submit = (from: string, to: string, piece?: string) => {
    const candidates = chess
      .moves({ square: from as any, verbose: true })
      .filter((move) => move.to === to);
    if (!candidates.length) return false;
    if (candidates.some((move) => move.promotion) && !piece) {
      setPromotion({ from, to });
      return false;
    }
    onMove?.(from + to + (piece || ""));
    setSelected(undefined);
    return true;
  };
  const squareStyles: Record<string, React.CSSProperties> = {};
  if (selected)
    squareStyles[selected] = {
      boxShadow: `inset 0 0 0 4px ${theme.board.selected}`,
    };
  for (const square of destinations)
    squareStyles[square] = {
      background: `radial-gradient(circle, ${theme.board.legal} 0 18%, transparent 20%)`,
    };
  if (lastMove && lastMove.length >= 4) {
    squareStyles[lastMove.slice(0, 2)] = { background: theme.board.lastFrom };
    squareStyles[lastMove.slice(2, 4)] = { background: theme.board.lastTo };
  }
  const pieces = useMemo<PieceRenderObject>(
    () =>
      Object.fromEntries(
        Object.entries(defaultPieces).map(([pieceType, DefaultPiece]) => [
          pieceType,
          (props: any) => {
            const white = pieceType.startsWith("w");
            const rawAvatar = assetUrl(white ? whiteAvatarUrl : blackAvatarUrl);
            const avatar = rawAvatar
              ? themedAvatarUrl(rawAvatar, theme.id)
              : "";
            const avatarStyle = white ? whiteAvatarStyle : blackAvatarStyle;
            return (
              <div className="piece-with-mask">
                <DefaultPiece {...props} />
                {avatar && (
                  <span className={`piece-mask ${avatarStyle}`}>
                    <img src={avatar} alt="" draggable={false} />
                  </span>
                )}
              </div>
            );
          },
        ]),
      ),
    [
      whiteAvatarUrl,
      blackAvatarUrl,
      whiteAvatarStyle,
      blackAvatarStyle,
      theme.id,
    ],
  );
  const options: ChessboardOptions = {
    id: "deathpit-board",
    position: fen,
    boardOrientation: orientation,
    showNotation: true,
    animationDurationInMs: 0,
    pieces,
    darkSquareStyle: { backgroundColor: theme.board.dark },
    lightSquareStyle: { backgroundColor: theme.board.light },
    squareStyles,
    allowDragging: interactive,
    allowDrawingArrows: !interactive,
    canDragPiece: ({ piece }) =>
      interactive &&
      piece.pieceType[0].toLowerCase() === (chess.turn() === "w" ? "w" : "b"),
    onPieceDrop: ({ sourceSquare, targetSquare }) =>
      targetSquare ? submit(sourceSquare, targetSquare) : false,
    onSquareClick: ({ piece, square }) => {
      if (!interactive) return;
      if (selected && submit(selected, square)) return;
      if (
        piece &&
        piece.pieceType[0].toLowerCase() === (chess.turn() === "w" ? "w" : "b")
      )
        setSelected(square);
      else setSelected(undefined);
    },
    boardStyle: {
      borderRadius: "2px",
      boxShadow: `0 0 0 2px ${theme.board.border}, 0 8px 24px ${theme.board.shadow}`,
    },
  };
  return (
    <div className="arena-board">
      <Chessboard options={options} />
      {promotion && (
        <div className="promotion">
          <span>Promote to</span>
          {[
            ["q", "♛"],
            ["r", "♜"],
            ["b", "♝"],
            ["n", "♞"],
          ].map(([code, glyph]) => (
            <button
              key={code}
              onClick={() => {
                submit(promotion.from, promotion.to, code);
                setPromotion(undefined);
              }}
            >
              {glyph}
            </button>
          ))}
          <button className="cancel" onClick={() => setPromotion(undefined)}>
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
