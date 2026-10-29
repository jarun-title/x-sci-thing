import React from 'react';
import {Easing, Interactive, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

const c = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// The glass, drawn in SVG. `level` 0 = full, 1 = lowered after boiling.
export const GlassArt: React.FC<{readonly fill: number; readonly draw: number; readonly lowered?: boolean}> = ({fill, draw, lowered}) => {
	const wl = lowered ? 470 : 375;
	return (
		<svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{position: 'absolute', inset: 0}}>
			<defs>
				<linearGradient id="wgrad" x1="0" y1="0" x2="0" y2="1">
					<stop offset="0" stopColor="#4fb0e4" stopOpacity={0.8} />
					<stop offset="1" stopColor="#14507e" stopOpacity={0.95} />
				</linearGradient>
			</defs>
			<g transform="translate(280 0)">
				<rect x={-2000} y={840} width={6000} height={600} fill="#0b111a" />
				<ellipse cx={960} cy={848} rx={300} ry={34} fill="#3f9fd6" opacity={0.12} />
				<g style={{transformBox: 'fill-box', transformOrigin: '50% 100%', scale: `1 ${fill}`}}>
					<path d={`M${960 - 199 + (lowered ? 15 : 0)} ${wl} L${960 + 199 - (lowered ? 15 : 0)} ${wl} L1120 816 L800 816 Z`} fill="url(#wgrad)" />
					<ellipse cx={960} cy={wl} rx={lowered ? 184 : 199} ry={16} fill="#9ad8f7" opacity={0.55} />
				</g>
				<path d="M750 240 L792 840 L1128 840 L1170 240" fill="none" stroke="#dbe9f3" strokeWidth={5} strokeLinejoin="round" strokeDasharray={1500} strokeDashoffset={1500 * (1 - draw)} />
				<ellipse cx={960} cy={240} rx={210} ry={20} fill="none" stroke="#dbe9f3" strokeWidth={3} opacity={0.7 * draw} />
			</g>
		</svg>
	);
};

const GlassSceneInner: React.FC<{readonly title: string; readonly subtitle: string}> = ({title, subtitle}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	return (
		<>
			<div
				style={{
					position: 'absolute',
					inset: 0,
					transformOrigin: '1240px 660px',
					scale: interpolate(frame, [3.95 * fps, 5.4 * fps], [1, 42], {...c, easing: Easing.bezier(0.55, 0, 1, 0.45), output: 'perceptual-scale'}),
				}}
			>
				<GlassArt
					draw={interpolate(frame, [0.15 * fps, 1.25 * fps], [0, 1], {...c, easing: Easing.bezier(0.65, 0, 0.35, 1)})}
					fill={interpolate(frame, [0.75 * fps, 2 * fps], [0, 1], {...c, easing: Easing.spring({damping: 200})})}
				/>
			</div>
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
					lineHeight: 0.95,
					color: '#e8eef4',
					width: 900,
					opacity: interpolate(frame, [1.2 * fps, 1.6 * fps, 3.6 * fps, 3.9 * fps], [0, 1, 1, 0], c),
					translate: interpolate(frame, [1.2 * fps, 1.8 * fps], ['0px 40px', '0px 0px'], {...c, easing: Easing.spring({damping: 200})}),
				}}
			>
				{title}
			</Interactive.Div>
			<Interactive.Div
				name="Subtitle"
				style={{
					position: 'absolute',
					left: 146,
					top: 500,
					fontFamily: '"DejaVu Sans Mono", monospace',
					fontSize: 78,
					color: '#7fb6d8',
					opacity: interpolate(frame, [1.6 * fps, 2 * fps, 3.6 * fps, 3.9 * fps], [0, 1, 1, 0], c),
				}}
			>
				{subtitle}
			</Interactive.Div>
			<div style={{position: 'absolute', inset: 0, backgroundColor: '#14507e', opacity: interpolate(frame, [5 * fps, 5.45 * fps], [0, 1], c)}} />
		</>
	);
};

export const GlassScene = Interactive.create({
	Component: GlassSceneInner,
	layout: 'absolute-fill',
	schema: {
		...Interactive.backgroundSchema,
		title: {type: 'string', default: 'A glass of water.', description: 'Title'},
		subtitle: {type: 'string', default: '250 mL · 20 °C', description: 'Subtitle'},
	},
});
