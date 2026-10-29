import {Composition, Folder} from 'remotion';
import {AtomScene} from './scenes/AtomScene';
import {GlassScene} from './scenes/GlassScene';
import {HeatScene} from './scenes/HeatScene';
import {MoleculesScene} from './scenes/MoleculesScene';
import {SteamScene} from './scenes/SteamScene';
import {Water} from './Water';

export const RemotionRoot: React.FC = () => {
	return (
		<>
			<Composition id="Water" component={Water} width={1920} height={1080} fps={30} durationInFrames={900} />
			<Folder name="Scenes">
				<Composition id="Glass" component={GlassScene} width={1920} height={1080} fps={30} durationInFrames={165} defaultProps={{title: 'A glass of water.', subtitle: '250 mL · 20 °C', style: {backgroundColor: '#070b12'}}} />
				<Composition id="Molecules" component={MoleculesScene} width={1920} height={1080} fps={30} durationInFrames={210} defaultProps={{title: 'One oxygen, two hydrogens.', style: {backgroundColor: '#14507e'}}} />
				<Composition id="Atom" component={AtomScene} width={1920} height={1080} fps={30} durationInFrames={150} defaultProps={{title: 'One oxygen atom.', style: {backgroundColor: '#05080f'}}} />
				<Composition id="Heat" component={HeatScene} width={1920} height={1080} fps={30} durationInFrames={210} defaultProps={{firstLine: 'Heat speeds them up.', secondLine: 'Bonds break. Vapor.', style: {backgroundColor: '#05080f'}}} />
				<Composition id="Steam" component={SteamScene} width={1920} height={1080} fps={30} durationInFrames={165} defaultProps={{title: '100 °C: water becomes gas.', style: {backgroundColor: '#06080d'}}} />
			</Folder>
		</>
	);
};
