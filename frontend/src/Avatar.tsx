import { useState } from "react";
import { assetUrl } from "./api";
import type { AvatarStyle } from "./types";
import { themedAvatarUrl, useTheme } from "./theme";

export function BotAvatar({
  src,
  name,
  style = "mask",
  className = "",
}: {
  src?: string | null;
  name: string;
  style?: AvatarStyle;
  className?: string;
}) {
  const [failed, setFailed] = useState(false);
  const { theme } = useTheme();
  const initial = name.trim()[0]?.toUpperCase() || "?";
  const raw = src ? assetUrl(src) : undefined;
  const resolved = raw ? themedAvatarUrl(raw, theme.id) : "";
  return (
    <span className={`bot-avatar ${style} ${className}`} aria-hidden="true">
      {src && !failed ? (
        <img
          key={resolved}
          src={resolved}
          alt=""
          onError={() => setFailed(true)}
        />
      ) : (
        <b>{initial}</b>
      )}
    </span>
  );
}
