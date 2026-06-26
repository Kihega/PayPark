/**
 * ParkiPay — Responsive scaling helpers
 * Baseline device: 375x812 (iPhone 11/X-class). Scales paddings, font
 * sizes, and heights so content fits without clipping on small phones
 * (e.g. 320-360px wide) and doesn't look tiny on large/tablet screens.
 */
import { Dimensions, PixelRatio } from 'react-native';

const { width: SCREEN_W, height: SCREEN_H } = Dimensions.get('window');

const BASE_W = 375;
const BASE_H = 812;

export type ScreenSize = 'small' | 'medium' | 'large';

/** < 360px wide (e.g. iPhone SE / small Android) */
export const isSmallDevice = SCREEN_W < 360;
/** 360-414px wide (most modern phones) */
export const isMediumDevice = SCREEN_W >= 360 && SCREEN_W < 414;
/** >= 414px wide (Plus/Max phones, small tablets) */
export const isLargeDevice = SCREEN_W >= 414;

export function getScreenSize(): ScreenSize {
  if (isSmallDevice) return 'small';
  if (isMediumDevice) return 'medium';
  return 'large';
}

/** Horizontal scale — widths, paddings, gaps */
export function scale(size: number): number {
  return (SCREEN_W / BASE_W) * size;
}

/** Vertical scale — heights, vertical spacing */
export function verticalScale(size: number): number {
  return (SCREEN_H / BASE_H) * size;
}

/**
 * Moderate scale — best for font sizes. `factor` controls how aggressively
 * it scales (0 = no scaling, 1 = full linear scaling). 0.5 is a good
 * middle-ground default so text shrinks a little on small phones without
 * becoming unreadable.
 */
export function moderateScale(size: number, factor = 0.5): number {
  return size + (scale(size) - size) * factor;
}

/** Caps OS-level accessibility font scaling so layouts don't blow out. */
export const MAX_FONT_SCALE = 1.2;

/** Rounds to the nearest device pixel — avoids blurry borders/text. */
export function pixelRound(size: number): number {
  return PixelRatio.roundToNearestPixel(size);
}
