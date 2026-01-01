import React, { ReactNode, useMemo } from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { TikTokPage } from "@remotion/captions";
import { TikTokPageView } from "./templates/TikTokPageView";
import { BottomKaraokeView } from "./templates/BottomKaraokeView";
import { TikTokStoryPageView } from "./templates/TikTokStoryPageView";

export type SubtitleTemplate = (opts: {
  page: TikTokPage;
  timeInMs: number;
  enterProgress: number;
}) => ReactNode;

const templates: Record<"tiktok" | "bottom_karaoke" | "tiktok_story", SubtitleTemplate> = {
  tiktok: TikTokPageView,
  bottom_karaoke: BottomKaraokeView,
  tiktok_story: TikTokStoryPageView
};

const SubtitlePage: React.FC<{
  readonly page: TikTokPage;
  readonly template: "tiktok" | "bottom_karaoke";
}> = ({ page, template }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const timeInMs = (frame / fps) * 1000;

  const enterProgress = spring({
    frame,
    fps,
    config: {
      damping: 200,
    },
    durationInFrames: 5,
  });

  const Template = useMemo(() => templates[template] ?? templates.tiktok, [template]);

  return (
    <AbsoluteFill>
      <Template enterProgress={enterProgress} page={page} timeInMs={timeInMs} />
    </AbsoluteFill>
  );
};

export default SubtitlePage;
