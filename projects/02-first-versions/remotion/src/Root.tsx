import React from 'react';
import { Composition } from 'remotion';
import { Water } from './Water';
export const Root: React.FC = () => (
  <Composition id="Water" component={Water} durationInFrames={900} fps={30} width={1280} height={720} />
);
