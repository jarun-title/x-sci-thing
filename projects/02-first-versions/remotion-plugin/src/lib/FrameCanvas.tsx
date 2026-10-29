import React, {useLayoutEffect, useRef} from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';

// A full-frame canvas redrawn from the current frame. Drawing is a pure function of time,
// so any frame renders on its own.
export const FrameCanvas: React.FC<{
	readonly draw: (ctx: CanvasRenderingContext2D, t: number, w: number, h: number) => void;
	readonly style?: React.CSSProperties;
}> = ({draw, style}) => {
	const frame = useCurrentFrame();
	const {fps, width, height} = useVideoConfig();
	const ref = useRef<HTMLCanvasElement>(null);
	useLayoutEffect(() => {
		const ctx = ref.current?.getContext('2d');
		if (ctx) draw(ctx, frame / fps, width, height);
	}, [draw, frame, fps, width, height]);
	return <canvas ref={ref} width={width} height={height} style={{position: 'absolute', inset: 0, ...style}} />;
};
