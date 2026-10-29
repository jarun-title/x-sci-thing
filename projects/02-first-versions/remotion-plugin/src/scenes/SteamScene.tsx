import React from 'react';
import {Easing, Interactive, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {GlassArt} from './GlassScene';

const c = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
// seeded wisp and bubble parameters
const R = (i: number) => {
	const x = Math.sin(i * 127.1 + 311.7) * 43758.5453;
	return x - Math.floor(x);
};
const WISPS = Array.from({length: 9}, (_, i) => ({x0: 1140 + (i % 5) * 50 + R(i) * 20, per: 2.4 + R(i + 9) * 1.2, ph: R(i + 19), amp: 18 + R(i + 29) * 20}));
const BUBBLES = Array.from({length: 26}, (_, i) => ({x: 1100 + R(i + 40) * 280, per: 0.9 + R(i + 70) * 1.1, ph: R(i + 99), r: 3 + R(i + 130) * 6}));

const SteamSceneInner: React.FC<{readonly title: string}> = ({title}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = frame / fps;
	return (
		<>
			<div
				style={{
					position: 'absolute',
					inset: 0,
					transformOrigin: '1240px 330px',
					scale: interpolate(frame, [0, 1.5 * fps], [3.2, 1], {...c, easing: Easing.bezier(0.45, 0, 0.55, 1), output: 'perceptual-scale'}),
				}}
			>
				<GlassArt draw={1} fill={1} lowered />
				<svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{position: 'absolute', inset: 0}}>
					<defs>
						<filter id="sblur" x="-50%" y="-50%" width="200%" height="200%">
							<feGaussianBlur stdDeviation={9} />
						</filter>
					</defs>
					<g fill="none" stroke="#dff3ff" strokeWidth={2}>
						{BUBBLES.map((b, i) => {
							const a = (t / b.per + b.ph) % 1;
							return <circle key={i} cx={b.x + Math.sin(a * 9 + i) * 6} cy={806 - a * 326} r={b.r * (0.6 + a * 0.6)} opacity={0.8 * Math.min(1, (1 - a) * 4)} />;
						})}
					</g>
					<g filter="url(#sblur)" fill="none" stroke="#eef4f8" strokeLinecap="round">
						{WISPS.map((w, i) => {
							const a = (t / w.per + w.ph) % 1, y = 450 - a * 380, x = w.x0 + Math.sin(a * 5 + i) * 20 * a;
							return <path key={i} d={`M${x} ${y} q ${w.amp} -55 0 -110 q ${-w.amp} -55 0 -110`} strokeWidth={16 + a * 26} opacity={0.55 * Math.sin(Math.PI * a)} />;
						})}
					</g>
				</svg>
			</div>
			<Interactive.Div
				name="Closing line"
				style={{
					position: 'absolute',
					left: 142,
					top: 178,
					width: 860,
					fontFamily: 'Inter, "DejaVu Sans", sans-serif',
					fontSize: 150,
					fontWeight: 900,
					letterSpacing: '-0.04em',
					lineHeight: 0.95,
					color: '#e8eef4',
					opacity: interpolate(frame, [1.35 * fps, 1.75 * fps], [0, 1], c),
					translate: interpolate(frame, [1.35 * fps, 1.95 * fps], ['0px 40px', '0px 0px'], {...c, easing: Easing.spring({damping: 200})}),
				}}
			>
				{title}
			</Interactive.Div>
		</>
	);
};

export const SteamScene = Interactive.create({
	Component: SteamSceneInner,
	layout: 'absolute-fill',
	schema: {
		...Interactive.backgroundSchema,
		title: {type: 'string', default: '100 °C: water becomes gas.', description: 'Closing line'},
	},
});
