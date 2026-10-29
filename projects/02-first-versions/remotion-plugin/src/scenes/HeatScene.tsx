import React, {useCallback, useMemo} from 'react';
import {Easing, Interactive, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {FrameCanvas} from '../lib/FrameCanvas';
import {clamp, drawMolecules} from '../lib/h2o';

const c = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const io = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const heatAt = (t: number) => 0.25 + 0.75 * io(clamp(t / 4.2));
const vapAt = (t: number) => clamp((t - 4.1) / 2.9);

const HeatSceneInner: React.FC<{readonly firstLine: string; readonly secondLine: string}> = ({firstLine, secondLine}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = frame / fps;
	// agitation clock: heat integrated once, looked up per frame
	const tau = useMemo(() => {
		const dt = 0.01, n = Math.ceil(7 / dt) + 2, arr = new Float32Array(n);
		for (let i = 1; i < n; i++) arr[i] = arr[i - 1] + dt * (1 + 3.2 * heatAt(i * dt));
		return (x: number) => {
			const k = clamp(x, 0, 7) / dt, i = Math.floor(k);
			return arr[i] + (arr[Math.min(i + 1, n - 1)] - arr[i]) * (k - i);
		};
	}, []);
	const draw = useCallback(
		(ctx: CanvasRenderingContext2D, tt: number, w: number, h: number) => {
			const back = 6 - 5 * (1 - Math.pow(1 - clamp(tt / 0.9), 4));
			drawMolecules(ctx, w, h, {tau: tau(tt) + 9, heat: heatAt(tt), vapor: vapAt(tt), zoom: back * (1 - 0.4 * clamp((tt - 4.2) / 2.8))});
		},
		[tau],
	);
	return (
		<>
			<div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 50%, #123a5c 0%, #0a2238 85%)'}} />
			<div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 110%, #b4481a 0%, #4a1e12 45%, #1a0d0b 90%)', opacity: interpolate(frame, [0, 4.2 * fps], [0.6, 1], {...c, easing: Easing.bezier(0.45, 0, 0.55, 1)})}} />
			<div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 50%, #151b26 0%, #06080d 85%)', opacity: interpolate(frame, [4.4 * fps, 6.6 * fps], [0, 1], {...c, easing: Easing.bezier(0.45, 0, 0.55, 1)})}} />
			<FrameCanvas draw={draw} style={{opacity: interpolate(frame, [0, 0.5 * fps], [0, 1], c)}} />
			<div style={{position: 'absolute', inset: 0, background: 'linear-gradient(to bottom, rgba(5,8,14,0.92) 0%, rgba(5,8,14,0.55) 30%, rgba(5,8,14,0) 50%, rgba(5,8,14,0) 62%, rgba(5,8,14,0.85) 100%)'}} />
			<Interactive.Div
				name="Heat line"
				style={{
					position: 'absolute',
					left: 142,
					top: 178,
					width: 1100,
					fontFamily: 'Inter, "DejaVu Sans", sans-serif',
					fontSize: 150,
					fontWeight: 900,
					letterSpacing: '-0.04em',
					lineHeight: 0.95,
					color: '#e8eef4',
					opacity: interpolate(frame, [0.7 * fps, 1.1 * fps, 3.5 * fps, 3.8 * fps], [0, 1, 1, 0], c),
					translate: interpolate(frame, [0.7 * fps, 1.3 * fps], ['0px 40px', '0px 0px'], {...c, easing: Easing.spring({damping: 200})}),
				}}
			>
				{firstLine}
			</Interactive.Div>
			<Interactive.Div
				name="Vapor line"
				style={{
					position: 'absolute',
					left: 142,
					top: 178,
					width: 1100,
					fontFamily: 'Inter, "DejaVu Sans", sans-serif',
					fontSize: 150,
					fontWeight: 900,
					letterSpacing: '-0.04em',
					lineHeight: 0.95,
					color: '#ffffff',
					opacity: interpolate(frame, [4.25 * fps, 4.65 * fps, 6.6 * fps, 6.9 * fps], [0, 1, 1, 0], c),
					translate: interpolate(frame, [4.25 * fps, 4.85 * fps], ['0px 40px', '0px 0px'], {...c, easing: Easing.spring({damping: 200})}),
				}}
			>
				{secondLine}
			</Interactive.Div>
			<Interactive.Div
				name="Temperature"
				style={{
					position: 'absolute',
					right: 142,
					bottom: 178,
					fontFamily: 'Inter, "DejaVu Sans", sans-serif',
					fontSize: 150,
					fontWeight: 900,
					letterSpacing: '-0.04em',
					color: '#ffb070',
					fontVariantNumeric: 'tabular-nums',
					transformOrigin: '100% 50%',
					scale: interpolate(frame, [4.2 * fps, 4.35 * fps, 4.9 * fps], [1, 1.14, 1], {...c, easing: [Easing.bezier(0.16, 1, 0.3, 1), Easing.spring({damping: 12})], output: 'perceptual-scale'}),
				}}
			>
				{Math.round(20 + 80 * heatAt(t))} °C
			</Interactive.Div>
		</>
	);
};

export const HeatScene = Interactive.create({
	Component: HeatSceneInner,
	layout: 'absolute-fill',
	schema: {
		...Interactive.backgroundSchema,
		firstLine: {type: 'string', default: 'Heat speeds them up.', description: 'First line'},
		secondLine: {type: 'string', default: 'Bonds break. Vapor.', description: 'Second line'},
	},
});
