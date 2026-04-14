$fn = 128;

// Zeiss Axio left-focus conical clamp pulley
// First-pass parametric concept:
// - two mirrored clamp halves
// - tapered inner bore matching measured focus knob
// - smooth outer pulley body sized for GT2 belt contact

knob_d_end = 34.12;
knob_d_base = 37.52;
knob_height = 26.5;

clearance = 0.4;
wall = 5.0;
pulley_outer_d = 54.0;
pulley_height = 30.0;
split_gap = 1.2;

clamp_ear_width = 10.0;
clamp_ear_depth = 8.0;
clamp_ear_height = pulley_height;
clamp_hole_d = 3.4;
nut_capture_w = 6.2;
nut_capture_h = 2.7;

module tapered_bore() {
    cylinder(
        h = knob_height + 1.0,
        d1 = knob_d_base + clearance,
        d2 = knob_d_end + clearance
    );
}

module pulley_body() {
    difference() {
        cylinder(h = pulley_height, d = pulley_outer_d);
        translate([0, 0, 1.5]) tapered_bore();
    }
}

module clamp_ears() {
    for (side = [-1, 1]) {
        translate([
            side * ((pulley_outer_d / 2) + (clamp_ear_width / 2) - 1.0),
            0,
            0
        ])
        cube([clamp_ear_width, clamp_ear_depth, clamp_ear_height], center = true);
    }
}

module clamp_hardware() {
    for (zpos = [pulley_height * 0.33, pulley_height * 0.66]) {
        translate([0, 0, zpos - pulley_height / 2]) {
            rotate([90, 0, 0])
            cylinder(h = pulley_outer_d + 30, d = clamp_hole_d, center = true);

            translate([-(pulley_outer_d / 2 + clamp_ear_width / 2), 0, 0])
            rotate([90, 0, 0])
            linear_extrude(height = nut_capture_h, center = true)
            polygon(points = [
                [ nut_capture_w / 2, 0],
                [ nut_capture_w / 4,  nut_capture_w * 0.433],
                [-nut_capture_w / 4,  nut_capture_w * 0.433],
                [-nut_capture_w / 2, 0],
                [-nut_capture_w / 4, -nut_capture_w * 0.433],
                [ nut_capture_w / 4, -nut_capture_w * 0.433]
            ]);
        }
    }
}

module split_cut() {
    translate([0, 0, 0])
    cube([pulley_outer_d + 40, split_gap, pulley_height + 2], center = true);
}

module half_part(side = 1) {
    intersection() {
        difference() {
            union() {
                translate([0, 0, pulley_height / 2]) pulley_body();
                translate([0, 0, pulley_height / 2]) clamp_ears();
            }
            translate([0, 0, pulley_height / 2]) split_cut();
            translate([0, 0, pulley_height / 2]) clamp_hardware();
        }
        translate([side * 100, 0, pulley_height / 2])
        cube([200, 200, pulley_height + 10], center = true);
    }
}

translate([-40, 0, 0]) half_part(-1);
translate([ 40, 0, 0]) mirror([1, 0, 0]) half_part(-1);
