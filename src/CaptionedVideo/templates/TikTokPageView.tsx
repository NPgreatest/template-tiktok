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

const DESIRED_FONT_SIZE = 120;
const HIGHLIGHT_COLOR = "#39E508";

export const TikTokPageView: SubtitleTemplate = ({
  enterProgress,
  page,
  timeInMs,
}) => {
  const { width } = useVideoConfig();
  const fittedText = fitText({
    fontFamily,
    text: page.text,
    withinWidth: width * 0.9,
    textTransform: "uppercase",
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
        <span
          style={{
            transform: makeTransform([
              scale(interpolate(enterProgress, [0, 1], [0.8, 1])),
              translateY(interpolate(enterProgress, [0, 1], [50, 0])),
            ]),
          }}
        >
          {page.tokens.map((t, index) => {
            const active = highlightedTokenIndex === index;

            return (
              <span
                key={t.fromMs}
                style={{
                  display: "inline",
                  whiteSpace: "pre",
                  color: active ? HIGHLIGHT_COLOR : "white",
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
