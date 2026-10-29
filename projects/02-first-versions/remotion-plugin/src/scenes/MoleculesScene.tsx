import React, {useCallback} from 'react';
import {Easing, Interactive, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {FrameCanvas} from '../lib/FrameCanvas';
import {centerGeometry, clamp, drawMolecules} from '../lib/h2o';

const c = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const easeOut = (x: number) => 1 - Math.pow(1 - x, 4);
const easeIn = (x: number) => x * x * x;

const MoleculesSceneInner: React.FC<{readonly title: string}> = ({title}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const draw = useCallback((ctx: CanvasRenderingContext2D, t: number, w: number, h: number) => {
		const zin = 0.35 + 0.65 * easeOut(clamp(t / 1.3));
		const dive = Math.exp(Math.log(7) * easeIn(clamp((t - 5.4) / 1.5)));
		drawMolecules(ctx, w, h, {tau: t + 3, heat: 0, vapor: 0, zoom: zin * dive, bondAlpha: clamp((t - 0.6) / 0.6)});
	}, []);
	const g = centerGeometry(1920, 5.2);
	const [ox, oy] = g.o;
	const labelIn = interpolate(frame, [2.2 * fps, 2.6 * fps, 5 * fps, 5.3 * fps], [0, 1, 1, 0], c);
	return (
		<>
			<div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 50%, #0f3d63 0%, #0a2742 80%)'}} />
			<FrameCanvas draw={draw} style={{opacity: interpolate(frame, [0, 0.6 * fps], [0.2, 1], c)}} />
			<div style={{position: 'absolute', inset: 0, background: 'linear-gradient(to bottom, rgba(5,12,22,0.8) 0%, rgba(5,12,22,0) 45%)'}} />
			<Interactive.Div
				name="Title"
				style={{
					position: 'absolute',
					left: 142,
					top: 178,
					width: 1640,
					fontFamily: 'Inter, "DejaVu Sans", sans-serif',
					fontSize: 150,
					fontWeight: 900,
					letterSpacing: '-0.04em',
					lineHeight: 0.95,
					color: '#e8eef4',
					opacity: interpolate(frame, [0.9 * fps, 1.3 * fps, 4.6 * fps, 4.9 * fps], [0, 1, 1, 0], c),
					translate: interpolate(frame, [0.9 * fps, 1.5 * fps], ['0px 40px', '0px 0px'], {...c, easing: Easing.spring({damping: 200})}),
				}}
			>
				{title}
			</Interactive.Div>
			<Interactive.Div
				name="Angle label"
				style={{
					position: 'absolute',
					left: ox - 120,
					top: oy + 90,
					fontFamily: '"DejaVu Sans Mono", monospace',
					fontSize: 78,
					fontWeight: 700,
					color: '#ffd27a',
					textShadow: '0 2px 12px rgba(0,0,0,0.85)',
					opacity: labelIn,
				}}
			>
				104.5°
			</Interactive.Div>
			<div
				style={{
					position: 'absolute',
					inset: 0,
					background: 'radial-gradient(circle at 50% 50%, #1b2840 0%, #05080f 60%)',
					opacity: interpolate(frame, [6.6 * fps, 6.95 * fps], [0, 1], c),
				}}
			/>
		</>
	);
};

export const MoleculesScene = Interactive.create({
	Component: MoleculesSceneInner,
	layout: 'absolute-fill',
	schema: {
		...Interactive.backgroundSchema,
		title: {type: 'string', default: 'One oxygen, two hydrogens.', description: 'Title'},
	},
});
