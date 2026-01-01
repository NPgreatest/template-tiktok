import React from "react";
import { AbsoluteFill, interpolate, useVideoConfig } from "remotion";
import { TheBoldFont } from "../../load-font";
import { fitText } from "@remotion/layout-utils";
import { makeTransform, scale, translateY } from "@remotion/animation-utils";
import type { SubtitleTemplate } from "../SubtitlePage";
import { getHighlightedTokenIndex } from "./helpers";

const fontFamily = TheBoldFont;

const container: React.CSSProperties = {
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
};

const DESIRED_FONT_SIZE = 82;

export const TikTokStoryPageView: SubtitleTemplate = ({
  enterProgress,
  page,
  timeInMs,
}) => {
  const { width } = useVideoConfig();
  const fittedText = fitText({
    fontFamily,
    text: page.text,
    withinWidth: width * 0.92,
  });

  const fontSize = Math.min(DESIRED_FONT_SIZE, fittedText.fontSize);
  const highlightedTokenIndex = getHighlightedTokenIndex({
    page,
    timeInMs,
  });

  return (
    <AbsoluteFill style={container}>
      <div
        style={{
          fontSize,
          color: "white",
          WebkitTextStroke: "20px black",
          paintOrder: "stroke",
          transform: makeTransform([
            scale(interpolate(enterProgress, [0, 1], [0.8, 1])),
            translateY(interpolate(enterProgress, [0, 1], [50, 0])),
          ]),
          fontFamily,
          textTransform: "uppercase",
        }}
      >
        <span>
          {page.tokens.map((t, index) => {
            const active = highlightedTokenIndex === index;

            return (
              <span
                key={t.fromMs}
                style={{
                  display: "inline",
                  whiteSpace: "pre",
                  color: "white", // 始终白色字体
                  WebkitTextStroke: "20px black", // 始终黑色描边
                  textShadow: active
                    ? "0 0 25px white, 0 0 40px white" // 高亮白色（发光）
                    : "none",
                  transition: "text-shadow 0.2s ease-out",
                }}
              >
                {t.text}
              </span>
            );
          })}
        </span>
      </div>
    </AbsoluteFill>
  );
};
