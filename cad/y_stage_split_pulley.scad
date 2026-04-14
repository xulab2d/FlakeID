$fn = 128;

// Zeiss Axio Y-stage split pulley
// Knob diameter measured: 32.93 mm

knob_d = 32.93;
clearance = 0.5;
pulley_outer_d = 50.0;
pulley_height = 18.0;
hub_height = 24.0;
split_gap = 1.0;

ear_width = 9.0;
ear_depth = 8.0;
hole_d = 3.4;
nut_capture_w = 6.2;
nut_capture_h = 2.7;

module body() {
    difference() {
        union() {
            cylinder(h = hub_height, d = pulley_outer_d - 4.0);
            translate([0, 0, (hub_height - pulley_height) / 2])
            cylinder(h = pulley_height, d = pulley_outer_d);
        }
        translate([0, 0, -1])
        cylinder(h = hub_height + 2, d = knob_d + clearance);
    }
}

module ears() {
    for (side = [-1, 1]) {
        translate([
            side * ((pulley_outer_d / 2) + (ear_width / 2) - 1.0),
            0,
            hub_height / 2
        ])
        cube([ear_width, ear_depth, hub_height], center = true);
    }
}

module hardware() {
    for (zpos = [hub_height * 0.35, hub_height * 0.7]) {
        translate([0, 0, zpos]) {
            rotate([90, 0, 0])
            cylinder(h = pulley_outer_d + 30, d = hole_d, center = true);

            translate([-(pulley_outer_d / 2 + ear_width / 2), 0, 0])
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
    translate([0, 0, hub_height / 2])
    cube([pulley_outer_d + 40, split_gap, hub_height + 2], center = true);
}

module half_part(side = 1) {
    intersection() {
        difference() {
            union() {
                body();
                ears();
            }
            split_cut();
            hardware();
        }
        translate([side * 100, 0, hub_height / 2])
        cube([200, 200, hub_height + 10], center = true);
    }
}

translate([-38, 0, 0]) half_part(-1);
translate([ 38, 0, 0]) mirror([1, 0, 0]) half_part(-1);
