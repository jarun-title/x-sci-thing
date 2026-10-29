from manim import *
import numpy as np

rng = np.random.default_rng(4)
BG = "#0b1220"
Text.set_default(font="DejaVu Sans")
WATER = "#3f9fd6"
O_COL, H_COL, HOT = "#e2584a", "#eef2f6", "#ff9a3c"
HALF = np.deg2rad(104.5 / 2)


def h2o(scale=1.0):
    o = Circle(radius=0.2 * scale, fill_color=O_COL, fill_opacity=1, stroke_width=0)
    h1 = Circle(radius=0.12 * scale, fill_color=H_COL, fill_opacity=1, stroke_width=0)
    h2 = h1.copy()
    d = 0.33 * scale
    h1.move_to(d * np.array([np.sin(HALF), -np.cos(HALF), 0]))
    h2.move_to(d * np.array([-np.sin(HALF), -np.cos(HALF), 0]))
    b1 = Line(ORIGIN, h1.get_center(), stroke_width=7 * scale, color=GREY_B)
    b2 = Line(ORIGIN, h2.get_center(), stroke_width=7 * scale, color=GREY_B)
    return VGroup(b1, b2, o, h1, h2)


class GlassToSteam(MovingCameraScene):
    def caption(self, n, title, sub):
        g = VGroup(
            Text(f"{n:02d} / 07", font="DejaVu Sans Mono", font_size=16, color=BLUE_B),
            Text(title, font_size=34, weight=BOLD),
            Text(sub, font_size=20, color=GREY_B),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        g.to_corner(DL, buff=0.5)
        return g

    def construct(self):
        self.camera.background_color = BG

        # ---------- 1. glass ----------
        glass = Polygon([-1.4, 2, 0], [1.4, 2, 0], [1.1, -2, 0], [-1.1, -2, 0], stroke_color=GREY_A, stroke_width=4)
        water = Polygon([-1.31, 0.9, 0], [1.31, 0.9, 0], [1.05, -1.9, 0], [-1.05, -1.9, 0], stroke_width=0, fill_color=WATER, fill_opacity=0.75)
        surface = Line([-1.31, 0.9, 0], [1.31, 0.9, 0], color=BLUE_A, stroke_width=3)
        table = Line([-7, -2, 0], [7, -2, 0], color=GREY_D)
        glass_grp = VGroup(table, water, surface, glass).shift(RIGHT * 1.5)
        cap = self.caption(1, "A glass of water", "About 250 mL at 20 °C")
        self.play(Create(table), DrawBorderThenFill(glass), run_time=1.2)
        self.play(FadeIn(water, shift=UP * 0.3), Create(surface), FadeIn(cap), run_time=1.2)
        self.wait(0.8)

        # ---------- 2. zoom ----------
        self.play(FadeOut(cap), run_time=0.4)
        self.camera.frame.save_state()
        target = water.get_center() + DOWN * 0.3
        self.play(self.camera.frame.animate.scale(0.02).move_to(target), run_time=2.5, rate_func=rate_functions.ease_in_expo)

        # ---------- 3. molecules ----------
        self.remove(table, water, surface, glass, glass_grp)
        self.camera.frame.restore()
        bg = Rectangle(width=16, height=10, fill_color="#0f3d63", fill_opacity=1, stroke_width=0)
        self.add(bg)

        heat = ValueTracker(0)
        vap = ValueTracker(0)
        clock = ValueTracker(0)
        ticker = Mobject()
        ticker.add_updater(lambda m, dt: clock.increment_value(dt * (1 + 3.5 * heat.get_value())))
        self.add(ticker)

        mols = VGroup()
        bases = []
        for r in range(-3, 4):
            for c in range(-6, 7):
                center = r == 0 and c == 0
                p = np.array([c * 1.15 + (0.575 if r % 2 else 0), r * 1.0, 0])
                if not center:
                    p += rng.uniform(-0.15, 0.15, 3) * [1, 1, 0]
                m = h2o()
                a0 = 0 if center else rng.uniform(0, TAU)
                m.rotate(a0, about_point=ORIGIN).move_to(ORIGIN)
                m.shift(p - m[2].get_center())
                m.base, m.a0, m.rot = p, a0, a0
                m.ph = rng.uniform(0, 7, 3)
                m.dir = np.array([rng.uniform(-1, 1), rng.uniform(0.6, 1.6), 0])
                m.spin = rng.uniform(-3, 3)
                mols.add(m)
        center_mol = mols[len(mols) // 2]

        def jiggle(m):
            t, h, v = clock.get_value(), heat.get_value(), vap.get_value()
            amp = 0.04 + 0.16 * h
            target = m.base + amp * np.array([np.sin(1.7 * t + m.ph[0]), np.cos(1.3 * t + m.ph[1]), 0]) + m.dir * 9 * v ** 1.8
            rot = m.a0 + (0.12 + 0.6 * h) * np.sin(1.1 * t + m.ph[2]) + m.spin * v * v * 6
            m.rotate(rot - m.rot, about_point=m[2].get_center())
            m.rot = rot
            m.shift(target - m[2].get_center())
            m[2].set_fill(interpolate_color(ManimColor(O_COL), ManimColor(HOT), h))

        for m in mols:
            m.add_updater(jiggle)

        # hydrogen bonds to nearest neighbour
        bonds = VGroup()
        for m in mols:
            others = [n for n in mols if n is not m]
            nb = min(others, key=lambda n: np.linalg.norm(n.base - m.base))
            ln = DashedLine(m[3].get_center(), nb[2].get_center(), color=BLUE_B, stroke_width=2, dash_length=0.06)
            ln.add_updater(lambda l, m=m, nb=nb: l.put_start_and_end_on(m[3].get_center(), nb[2].get_center()) if np.linalg.norm(m[3].get_center() - nb[2].get_center()) > 0.01 else None)
            bonds.add(ln)

        mols.scale(0.3)  # appear small, then grow as if still zooming
        for m in mols:
            m.base = m.base * 0.3
        self.play(FadeIn(mols), run_time=0.4)
        for m in mols:
            m.base = m.base / 0.3
        self.play(mols.animate.scale(1 / 0.3), run_time=1.2, rate_func=rate_functions.ease_out_cubic)
        self.add(bonds)
        self.bring_to_front(mols)
        bonds.set_opacity(0)
        self.play(bonds.animate.set_opacity(0.6), run_time=0.6)

        cap = self.caption(2, "Water molecules", "H₂O · oxygen red, hydrogen white")
        cap.add_background_rectangle(color=BG, opacity=0.7, buff=0.15)
        angle_lbl = Text("104.5°", font_size=22, color=YELLOW).next_to(center_mol[2], UP, buff=0.12)
        hb_lbl = Text("hydrogen bond", font_size=18, color=BLUE_B).move_to(RIGHT * 2.4 + UP * 0.55)
        self.play(FadeIn(cap), FadeIn(angle_lbl), FadeIn(hb_lbl), run_time=0.8)
        self.wait(2)

        # ---------- 4. into the atom ----------
        self.play(FadeOut(cap), FadeOut(angle_lbl), FadeOut(hb_lbl), run_time=0.4)
        self.camera.frame.save_state()
        self.play(self.camera.frame.animate.scale(0.06).move_to(center_mol[2].get_center()), run_time=2.2, rate_func=rate_functions.ease_in_expo)
        self.remove(mols, bonds, bg)
        self.camera.frame.restore()

        nucleus = VGroup()
        for i in range(16):
            ang = i * 2.39996
            rr = 0.07 * np.sqrt(i + 0.5)
            nucleus.add(Circle(radius=0.075, fill_color=O_COL if i % 2 == 0 else GREY_B, fill_opacity=1, stroke_width=0).move_to([rr * np.cos(ang), rr * np.sin(ang), 0]))
        shell1 = Circle(radius=1.1, color=BLUE_D, stroke_width=2)
        shell2 = Circle(radius=2.3, color=BLUE_D, stroke_width=2)
        phase = ValueTracker(0)
        phase.add_updater(lambda m, dt: m.increment_value(dt * (1 + 4 * heat.get_value())))

        def electrons():
            g = VGroup()
            p = phase.get_value()
            col = interpolate_color(ManimColor("#9fd6f2"), ManimColor(HOT), heat.get_value())
            for k in range(2):
                a = p * 1.6 + k * PI
                g.add(Dot([1.1 * np.cos(a), 1.1 * np.sin(a), 0], radius=0.09, color=col))
            for k in range(6):
                a = -p + k * TAU / 6
                g.add(Dot([2.3 * np.cos(a), 2.3 * np.sin(a), 0], radius=0.09, color=col))
            return g

        elec = always_redraw(electrons)
        atom = VGroup(shell1, shell2, nucleus).scale(0.5)
        self.add(phase)
        cap = self.caption(3, "An oxygen atom", "8 protons · 8 neutrons · 8 electrons")
        l1 = Text("nucleus (enlarged)", font_size=18, color=GREY_B).next_to(ORIGIN, DR, buff=0.35)
        l2 = Text("2 electrons", font_size=18, color=BLUE_B).move_to([1.6, 0.9, 0])
        l3 = Text("6 electrons", font_size=18, color=BLUE_B).move_to([2.6, 2.1, 0])
        note = Text("Bohr model: a simplified picture", font_size=16, color=GREY_C).to_corner(UR, buff=0.5)
        self.play(atom.animate.scale(2), FadeIn(elec), run_time=1.0)
        self.play(FadeIn(cap), FadeIn(l1), FadeIn(l2), FadeIn(l3), FadeIn(note), run_time=0.8)
        self.wait(1.5)

        # ---------- 5. heating ----------
        tube = RoundedRectangle(width=0.32, height=3, corner_radius=0.16, stroke_color=GREY_B, stroke_width=2)
        tube.to_edge(RIGHT, buff=0.9).shift(DOWN * 0.3)
        tcol = lambda: interpolate_color(ManimColor("#5fb8e6"), ManimColor(HOT), heat.get_value())
        temp = always_redraw(lambda: Text(f"{20 + 80 * heat.get_value():.0f} °C", font="DejaVu Sans", font_size=34, weight=BOLD, color=tcol()).next_to(tube, UP, buff=0.2))
        fill = always_redraw(lambda: Rectangle(width=0.18, height=0.05 + 2.8 * (0.25 + 0.75 * heat.get_value()), fill_color=tcol(), fill_opacity=1, stroke_width=0).align_to(tube, DOWN).shift(UP * 0.07).set_x(tube.get_x()))
        new_cap = self.caption(4, "Heating up", "Energy makes everything move faster")
        self.play(FadeOut(note), FadeIn(tube), FadeIn(fill), FadeIn(temp), Transform(cap, new_cap), run_time=0.8)
        self.play(heat.animate.set_value(0.35), run_time=2.5, rate_func=linear)

        # back to molecules
        self.play(FadeOut(VGroup(atom, l1, l2, l3)), FadeOut(elec), FadeOut(cap), run_time=0.6)
        self.remove(elec, phase)
        bg.set_fill(interpolate_color(ManimColor("#0f3d63"), ManimColor("#3a2a2a"), 0.35))
        bg.add_updater(lambda b: b.set_fill(interpolate_color(interpolate_color(ManimColor("#0f3d63"), ManimColor("#4a2a1e"), heat.get_value()), ManimColor("#080c14"), min(1, vap.get_value() * 1.5))))
        self.add(bg, bonds, mols)
        self.bring_to_front(tube, fill, temp)
        mols.set_opacity(0); bonds.set_opacity(0)
        cap = self.caption(5, "Molecules speed up", "Hydrogen bonds stretch and snap")
        cap.add_background_rectangle(color=BG, opacity=0.7, buff=0.15)
        self.play(mols.animate.set_opacity(1), bonds.animate.set_opacity(0.6), FadeIn(cap), run_time=0.8)
        self.play(heat.animate.set_value(1), bonds.animate.set_opacity(0.15), run_time=4, rate_func=linear)
        boil = Text("100 °C · boiling", font_size=20, color=HOT).next_to(tube, DOWN, buff=0.2)
        self.play(FadeIn(boil), run_time=0.4)

        # ---------- 6. vapor ----------
        new_cap = self.caption(6, "Bonds break", "Molecules escape as water vapor")
        new_cap.add_background_rectangle(color=BG, opacity=0.7, buff=0.15)
        self.play(Transform(cap, new_cap), FadeOut(bonds), run_time=0.6)
        self.play(vap.animate.set_value(1), run_time=3.5, rate_func=rate_functions.ease_in_quad)

        # ---------- 7. steam ----------
        for m in mols:
            m.clear_updaters()
        self.remove(mols, bg)
        glass_grp.shift(LEFT * 1.5)
        water2 = Polygon([-1.24, 0.3, 0], [1.24, 0.3, 0], [1.05, -1.9, 0], [-1.05, -1.9, 0], stroke_width=0, fill_color=WATER, fill_opacity=0.75)
        surface2 = Line([-1.24, 0.3, 0], [1.24, 0.3, 0], color=BLUE_A, stroke_width=3)
        glass_final = VGroup(table, water2, surface2, glass)
        clock2 = ValueTracker(0)
        clock2.add_updater(lambda m, dt: m.increment_value(dt))

        def steam():
            g = VGroup()
            t = clock2.get_value()
            for i, x0 in enumerate([-0.7, 0, 0.7]):
                for k in range(2):
                    s = (t * 0.45 + i * 0.33 + k * 0.5) % 1
                    y0 = 2.1 + s * 2.2
                    curve = ParametricFunction(lambda u: np.array([x0 + 0.18 * np.sin(u * 2 * PI + t * 2 + i), y0 + u * 1.1, 0]), t_range=[0, 1], color=GREY_A, stroke_width=4)
                    curve.set_stroke(opacity=np.sin(PI * s) * 0.9)
                    g.add(curve)
            return g

        steam_m = always_redraw(steam)
        new_cap = self.caption(7, "Steam", "Liquid becomes gas at 100 °C")
        self.add(clock2)
        self.play(FadeIn(glass_final), FadeIn(steam_m), Transform(cap, new_cap), run_time=1.0)
        self.wait(3.5)
        self.play(*[FadeOut(m) for m in self.mobjects if m is not clock2 and m is not ticker], run_time=1)
