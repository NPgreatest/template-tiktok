import { TikTokPage } from "@remotion/captions";

export const getHighlightedTokenIndex = ({
  page,
  timeInMs,
}: {
  page: TikTokPage;
  timeInMs: number;
}) => {
  const absoluteTime = page.startMs + timeInMs;
  return page.tokens.findIndex(
    (token) => token.fromMs <= absoluteTime && token.toMs > absoluteTime,
  );
};
