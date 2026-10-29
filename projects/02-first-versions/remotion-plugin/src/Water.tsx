import {Audio} from '@remotion/media';
import {lightLeak} from '@remotion/effects/light-leak';
import React from 'react';
import {Sequence, Solid, staticFile, Track, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {AtomScene} from './scenes/AtomScene';
import {GlassScene} from './scenes/GlassScene';
import {HeatScene} from './scenes/HeatScene';
import {MoleculesScene} from './scenes/MoleculesScene';
import {SteamScene} from './scenes/SteamScene';

// A warm light leak over the moment the water reaches 100 °C.
const BoilFlash: React.FC = () => {
	const frame = useCurrentFrame();
	const {durationInFrames, width, height} = useVideoConfig();
	return (
		<Solid
			width={width}
			height={height}
			style={{mixBlendMode: 'screen', opacity: 0.55}}
			effects={[lightLeak({seed: 3, hueShift: 20, progress: interpolate(frame, [0, durationInFrames - 1], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})})]}
		/>
	);
};

export const Water: React.FC = () => {
	const {fps} = useVideoConfig();
	return (
		<>
			<Track name="Scenes">
				<GlassScene name="Glass" durationInFrames={5.5 * fps} title="A glass of water." subtitle="250 mL · 20 °C" style={{backgroundColor: '#070b12'}} />
				<MoleculesScene name="Molecules" from={5.5 * fps} durationInFrames={7 * fps} title="One oxygen, two hydrogens." style={{backgroundColor: '#14507e'}} />
				<AtomScene name="Atom" from={12.5 * fps} durationInFrames={5 * fps} title="One oxygen atom." style={{backgroundColor: '#05080f'}} />
				<HeatScene name="Heat" from={17.5 * fps} durationInFrames={7 * fps} firstLine="Heat speeds them up." secondLine="Bonds break. Vapor." style={{backgroundColor: '#05080f'}} />
				<SteamScene name="Steam" from={24.5 * fps} durationInFrames={5.5 * fps} title="100 °C: water becomes gas." style={{backgroundColor: '#06080d'}} />
			</Track>
			<Sequence name="Boil flash" from={21.5 * fps} durationInFrames={1.6 * fps}>
				<BoilFlash />
			</Sequence>
			<Track name="Music">
				<Audio name="Ambient bed" src={staticFile('audio/bed.wav')} durationInFrames={30 * fps} volume={0.413} />
			</Track>
			<Track name="Whooshes">
				<Audio name="Dive into water" src={staticFile('sfx/whoosh-cinematic.mp3')} from={2.78 * fps} durationInFrames={5.5 * fps} volume={0.315} />
				<Audio name="Into the atom" src={staticFile('sfx/whoosh-short.mp3')} from={12.27 * fps} durationInFrames={0.57 * fps} volume={0.375} />
				<Audio name="Out of the atom" src={staticFile('sfx/whoosh.mp3')} from={17.27 * fps} durationInFrames={0.57 * fps} volume={0.338} />
			</Track>
			<Track name="Riser">
				<Audio name="Riser to boil" src={staticFile('sfx/riser.mp3')} from={18.45 * fps} durationInFrames={3.3 * fps} volume={0.24} />
			</Track>
			<Track name="Hits">
				<Audio name="100 °C hit" src={staticFile('sfx/impact-bass-1.mp3')} from={21.66 * fps} durationInFrames={2.1 * fps} volume={0.413} />
			</Track>
			<Track name="Boiling">
				<Audio name="Boiling water" src={staticFile('audio/boil.wav')} from={17.5 * fps} durationInFrames={12.5 * fps} volume={0.562} />
			</Track>
		</>
	);
};
