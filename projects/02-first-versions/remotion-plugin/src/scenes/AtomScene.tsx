import React, {useCallback} from 'react';
import {Easing, Interactive, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {FrameCanvas} from '../lib/FrameCanvas';
import {clamp, drawAtom} from '../lib/h2o';

const c = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const heatAt = (t: number) => 0.25 * clamp((t - 2.9) / 2.1);

const AtomSceneInner: React.FC<{readonly title: string}> = ({title}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = frame / fps;
	const draw = useCallback((ctx: CanvasRenderingContext2D, tt: number, w: number, h: number) => {
		drawAtom(ctx, w, h, {t: tt, heat: heatAt(tt), scale: 1.05 + 0.45 * (1 - Math.pow(1 - clamp(tt / 1.4), 4))});
	}, []);
	return (
		<>
			<div style={{position: 'absolute', inset: 0, background: 'radial-gradient(circle at 50% 50%, rgba(63,159,214,0.28) 0%, rgba(5,8,15,0) 38%)'}} />
			<div
				style={{
					position: 'absolute',
					inset: 0,
					background: 'radial-gradient(circle at 50% 50%, rgba(255,128,48,0.42) 0%, rgba(120,40,10,0.25) 40%, rgba(5,8,15,0) 75%)',
					opacity: interpolate(frame, [3 * fps, 4.6 * fps], [0, 1], {...c, easing: Easing.bezier(0.45, 0, 0.55, 1)}),
				}}
			/>
			<FrameCanvas
				draw={draw}
				style={{
					transformOrigin: '960px 540px',
					scale: interpolate(frame, [4.4 * fps, 4.95 * fps], [1, 0.12], {...c, easing: Easing.bezier(0.55, 0, 1, 0.45), output: 'perceptual-scale'}),
					opacity: interpolate(frame, [0, 0.6 * fps, 4.75 * fps, 4.95 * fps], [0, 1, 1, 0], c),
				}}
			/>
			<Interactive.Div
				name="Title"
				style={{
					position: 'absolute',
					left: 142,
					top: 178,
					fontFamily: 'Inter, "DejaVu Sans", sans-serif',
					fontSize: 150,
					fontWeight: 900,
					letterSpacing: '-0.04em',
					color: '#e8eef4',
					opacity: interpolate(frame, [0.5 * fps, 0.9 * fps, 2.6 * fps, 2.9 * fps], [0, 1, 1, 0], c),
					translate: interpolate(frame, [0.5 * fps, 1.1 * fps], ['0px 40px', '0px 0px'], {...c, easing: Easing.spring({damping: 200})}),
				}}
			>
				{title}
			</Interactive.Div>
			<Interactive.Div
				name="Cloud label"
				style={{
					position: 'absolute',
					left: 1240,
					top: 820,
					fontFamily: '"DejaVu Sans Mono", monospace',
					fontSize: 60,
					color: '#9fd6f2',
					opacity: interpolate(frame, [1.3 * fps, 1.6 * fps, 2.6 * fps, 2.9 * fps], [0, 1, 1, 0], c),
				}}
			>
				8 electrons
			</Interactive.Div>
			<Interactive.Div
				name="Temperature"
				style={{
					position: 'absolute',
					right: 142,
					top: 178,
					fontFamily: 'Inter, "DejaVu Sans", sans-serif',
					fontSize: 150,
					fontWeight: 900,
					letterSpacing: '-0.04em',
					color: '#ffb070',
					fontVariantNumeric: 'tabular-nums',
					opacity: interpolate(frame, [2.9 * fps, 3.2 * fps], [0, 1], c),
				}}
			>
				{Math.round(20 + 80 * heatAt(t))} °C
			</Interactive.Div>
		</>
	);
};

export const AtomScene = Interactive.create({
	Component: AtomSceneInner,
	layout: 'absolute-fill',
	schema: {
		...Interactive.backgroundSchema,
		title: {type: 'string', default: 'One oxygen atom.', description: 'Title'},
	},
});
