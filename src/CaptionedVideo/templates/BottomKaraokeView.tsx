import React from "react";
import { AbsoluteFill, useVideoConfig } from "remotion";
import { fitText } from "@remotion/layout-utils";
import type { SubtitleTemplate } from "../SubtitlePage";
import { TheBoldFont } from "../../load-font";
import { getHighlightedTokenIndex } from "./helpers";

const BACKGROUND = "rgba(0, 0, 0, 0.35)";
const HIGHLIGHT_COLOR = "#00E5FF";
const STROKE = "3px rgba(0, 0, 0, 0.8)";
const DESIRED_FONT_SIZE = 82;

export const BottomKaraokeView: SubtitleTemplate = ({
  enterProgress: _enterProgress,
  page,
  timeInMs,
}) => {
  const { width } = useVideoConfig();
  const fitted = fitText({
    fontFamily: TheBoldFont,
    text: page.text,
    withinWidth: width * 0.92,
  });
  const fontSize = Math.min(DESIRED_FONT_SIZE, fitted.fontSize);
  const highlightedTokenIndex = getHighlightedTokenIndex({
    page,
    timeInMs,
  });

  return (
    <AbsoluteFill
      style={{
        alignItems: "center",
        display: "flex",
        justifyContent: "center",
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          position: "absolute",
          bottom: 72,
          width: "100%",
          display: "flex",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            background: BACKGROUND,
            borderRadius: 8,
            padding: "12px 28px",
            maxWidth: width * 0.92,
            fontFamily: TheBoldFont,
            fontSize,
            lineHeight: 1.15,
            color: "white",
            WebkitTextStroke: STROKE,
            textAlign: "center",
            textTransform: "none",
            boxShadow: "0 6px 20px rgba(0, 0, 0, 0.25)",
          }}
        >
          {page.tokens.map((token, index) => {
            const active = highlightedTokenIndex === index;
            return (
              <span
                key={token.fromMs}
                style={{
                  display: "inline",
                  whiteSpace: "pre-wrap",
                  color: active ? HIGHLIGHT_COLOR : "white",
                  transition: "color 120ms linear, text-shadow 120ms linear",
                  textShadow: active
                    ? "0 0 12px rgba(0, 229, 255, 0.7)"
                    : "0 0 6px rgba(0, 0, 0, 0.45)",
                }}
              >
                {token.text}
              </span>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
