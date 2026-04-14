# Zeiss Axio Retrofit BOM

Purchase guide and printed-parts outline for a reversible motorized retrofit of the `Zeiss Axio` manual microscope, aimed at tiled `X/Y` scanning plus motorized `focus`.

## Zeiss Axio Measurements Collected

Current microscope measurements provided for this stand:

- `focus knob`
  - smooth, slightly conical
  - `34.12 mm` diameter at end
  - `37.52 mm` diameter at base
  - `26.5 mm` axial length
  - duplicated on left and right side, both drive the same focus mechanism
- `X stage knob`
  - knurled
  - `27.8 mm` diameter
- `Y stage knob`
  - knurled
  - `32.93 mm` diameter
  - stage knobs are vertically oriented on downward shafts

These measurements are enough to narrow the coupling design considerably.

## Retrofit Strategy

Use a reversible belt-driven retrofit:

- `X/Y`: printed pulleys on the microscope stage knobs, driven by two stepper motors through GT2 belts.
- `Focus`: separate motor module on the fine-focus knob, preferably with a belt or friction drive and a disengage lever.
- `No drilling`: mount to existing screws, clamp points, or a custom wraparound bracket.
- `Manual use preserved`: motors should be removable or mechanically disengageable.

With the measured Zeiss Axio knobs, the best interpretation is:

- `focus`: a semi-permanent printed sleeve or clamp on the `left` focus knob is reasonable because the right focus knob remains available for manual use.
- `X/Y`: do not rely on bare belts riding directly on the knurled knobs as the primary final solution. It may work for a rough prototype, but it will not be the most repeatable or least-wear option.

Recommended Zeiss Axio-specific strategy:

- `focus`: printed conical clamp pulley on the left knob
- `X/Y`: printed split-clamp pulleys that fit over the knurled knobs

## Reference Open Hardware

- `openUC2 Motorized XY Table`
  - https://github.com/openUC2/UC2-Motorized-XY-Table
- `openUC2 MicronStage`
  - https://github.com/openUC2/UC2-MicronStage
- `openUC2 XYZ stage docs`
  - https://openuc2.github.io/docs/Electronics/XYZStage/
- `OpenFlexure motor references`
  - https://rwb27.github.io/openflexure_microscope/docs/5_motors.html

These are references for architecture and mechanics. You will still need Zeiss Axio-specific printed geometry.

## Recommended Purchase Paths

### Path A: Budget, Flexible, DIY Electronics

This is the best fit if you are comfortable wiring and tuning current limits yourself.

#### Controller / Drivers

- `Arduino Uno Rev3`
  - Official store: https://store.arduino.cc/collections/arduino/products/arduino-uno-rev3
  - Reference price seen: about `€19`
- `CNC Shield V3`
  - Example product: https://handsontec.com/index.php/product/cnc-shield-v3-for-arduino/
  - Example alternative: https://www.crcibernetica.com/cnc-shield-v3/
  - Typical price: about `$3-$10`
- `DRV8825 stepper drivers`, `3x`
  - Pololu: https://www.pololu.com/product/2133/
  - Soldered-header version: https://www.pololu.com/product/2982
  - Reference price seen: about `$16-$17` each

#### Motors

- `X/Y motors`: `2x` standard `NEMA 17` stepper motors, 5 mm shaft
  - OpenBuilds NEMA 17: https://us.openbuilds.com/nema-17-stepper-motor/
  - Reference price seen: about `$18` each
- `Focus motor`: `1x` compact `NEMA 11` stepper motor, 5 mm shaft
  - Pololu NEMA 11: https://www.pololu.com/product/1205/specs
  - Reference price seen: about `$40`

#### Motion Hardware

- `GT2 6 mm open belt`
  - RobotDigg: https://www.robotdigg.com/product/10/Open-Ended-6mm-Width-GT2-Belt
  - Tronxy 2 m example: https://www.tronxy3d.com/products/tronxy-2-meter-gt2-6mm-open-timing-belt-width-6mm-gt2-belt
  - Typical price: about `$2-$10` depending on length/source
- `GT2 20-tooth, 5 mm bore pulleys`
  - ServoCity: https://www.servocity.com/2mm-pitch-gt2-pinion-timing-pulley-5mm-bore-20-tooth/
  - RobotShop listing: https://www.robotshop.com/products/servocity-2mm-pitch-gt2-pinion-timing-pulley-5mm-bore-20-tooth
  - Typical price: about `$7-$8` each from branded sellers, cheaper from generic sellers
- `Optional geared X/Y motor upgrade`
  - Automation Technologies 5:1 geared NEMA 17: https://www.automationtechnologiesinc.com/products-page/nema17/nema-17-geared-stepper-motor
  - StepperOnline 5:1 geared NEMA 17: https://www.omc-stepperonline.com/nema-17-stepper-motor-l-39mm-gear-ratio-5-1-high-precision-planetary-gearbox-17hs15-1684s-hg5
  - Use this if the manual Zeiss Axio stage feels too stiff for plain NEMA 17 motors

#### Power / Switches / Print Hardware

- `12 V 5 A supply`
  - Adafruit: https://www.adafruit.com/product/352
  - Reference price seen: about `$25`
- `Limit switches`, optional but recommended for homing on `X` and `Y`
  - OpenBuilds Xtension limit switch: https://us.openbuilds.com/xtension-limit-switch-kit/
  - Reference price seen: about `$8` each
- `M3 heat-set inserts`
  - Adafruit M3 x 3 mm: https://www.adafruit.com/product/4256
  - Adafruit M3 x 4 mm: https://www.adafruit.com/product/4255
  - Reference price seen: about `$6` per 50-pack

### Path B: Cleaner, Higher-Cost, Less Wiring

This is better if you want a cleaner controller and easier long-term integration.

#### Controller

- `OpenBuilds BlackBox X32`
  - Product: https://us.openbuilds.com/BlackBox-Motion-Control-System-X32
  - Specs/docs: https://docs.openbuilds.com/doku.php?id=docs%3Ablackbox-x32%3Astart
  - Reference price seen: about `$240`

#### Motors / Motion Hardware

Same motor and belt hardware as Path A, but the BlackBox replaces the Arduino + CNC shield + DRV8825 stack.

## What To Buy

### Minimal First Build

- `2x` NEMA 17 motors for `X/Y`
- `1x` NEMA 11 motor for `focus`
- `1x` Arduino Uno
- `1x` CNC Shield V3
- `3x` DRV8825
- `1x` 12 V 5 A power supply
- `3x` GT2 20T 5 mm pulleys
- `2-5 m` GT2 6 mm belt
- `2-3x` limit switches
- `1x` M3 screw assortment
- `1x` M3 nut assortment or heat-set inserts

### If X/Y Torque Is Marginal

Upgrade only the `X/Y` motors to geared `NEMA 17` and keep the rest unchanged.

## 3D Printed Parts Required

These are the parts I would expect to print in PLA for a Zeiss Axio-specific retrofit.

### X/Y Stage Assembly

- `Zeiss Axio X-axis split-clamp pulley`, sized to `27.8 mm` knob diameter
- `Zeiss Axio Y-axis split-clamp pulley`, sized to `32.93 mm` knob diameter
- `left motor bracket`
- `right motor bracket`
- `bridge plate or shared bracket` if both motors mount to one printed frame
- `belt tensioner blocks`
- `idler mounts` if you need belt wrap or clearance
- `knob clamps / split collars` to mount pulleys without glue
- `cable clips`
- `stage-side limit switch mounts`

### Focus Assembly

- `focus motor bracket`
- `Zeiss Axio focus conical clamp pulley` for the left focus knob
- `swing-arm or tensioner for engage/disengage`
- `stop block for repeatable engagement`
- `focus limit switch mount` if you decide to add one

### Electronics / Enclosure

- `controller enclosure`
- `power entry bracket`
- `driver cooling shroud` if using discrete drivers
- `USB strain relief`

## PLA Guidance

PLA is acceptable for this build if:

- microscope is indoors and not near strong heat sources,
- motor currents and speeds stay moderate,
- structural printed parts use conservative print settings.

Recommended starting print settings:

- `4-5` perimeters
- `40-60%` infill for brackets and knob pulleys
- at least `0.2 mm` layer height
- avoid long, thin cantilevers
- use `M3` hardware and heat-set inserts in high-stress joints

Do not print belts. Buy real GT2 belts.

## Estimated Cost

### Budget Range

Using:

- Arduino + CNC shield + DRV8825
- standard `NEMA 17` for `X/Y`
- `NEMA 11` for focus
- purchased GT2 belts/pulleys

Expected total:

- about `$220-$320`

This assumes you are printing your own brackets and not buying a premium controller.

### Mid / Safer Range

Using:

- Arduino + CNC shield + DRV8825
- geared `NEMA 17` for `X/Y`
- `NEMA 11` for focus

Expected total:

- about `$300-$420`

### Premium Range

Using:

- OpenBuilds `BlackBox X32`
- geared `NEMA 17` for `X/Y`
- `NEMA 11` for focus

Expected total:

- about `$420-$650`

These ranges exclude filament, printer ownership, tools already on hand, and microscope-specific redesign time.

## Parts Most Likely To Need Custom Zeiss Axio CAD

- stage motor bracket geometry
- `27.8 mm` X-knob pulley geometry and clamp gap
- `32.93 mm` Y-knob pulley geometry and clamp gap
- focus motor bracket geometry
- conical focus sleeve geometry for `34.12 mm` to `37.52 mm` taper over `26.5 mm`
- any non-slip manual disengage feature

## Zeiss Axio-Specific Mechanical Recommendation

### Focus

Your focus geometry is favorable for a printed attachment.

Recommended design:

- a `two-piece conical clamp sleeve` that matches the taper of the left focus knob
- outer pulley teeth or a timing-belt groove integrated into that sleeve
- two or three `M3` clamp screws across the split line
- a thin internal friction liner if needed
  - `TPU` would be ideal, but if you only have PLA, start with bare PLA and add a thin rubber tape or friction tape only if it slips

Why this is the right direction:

- the knob is smooth, so a direct belt on the native surface is less reliable
- the conical shape actually helps a custom clamp stay axially located
- using the `left` knob leaves the `right` knob free for manual focus

I would not use a bare friction wheel as the first choice here. A printed conical clamp pulley is better.

### X/Y Stage

Your first instinct is understandable, but I would not plan on the belts contacting the knurled knobs directly in the final build.

It may work temporarily because the knurling adds grip, but there are three problems:

- the effective drive diameter is not precisely controlled
- belt tracking can wander on a bare knob
- repeated belt tension on the microscope knob surface is harder to reproduce and may wear badly

Recommended design:

- `split-clamp pulleys` that sit over the knurled knobs
- inner bore sized slightly under nominal diameter so the clamp grips the knurling
- shallow relief or texture inside the bore to key into the knurl
- flanged outer pulley profile so the GT2 belt tracks properly

This gives you:

- known pulley diameter for motion calibration
- less slip
- better belt alignment
- cleaner reversibility

### Vertical Shaft Orientation

Because the `X/Y` knobs are on vertical shafts, the motor arrangement should likely be:

- motor shafts horizontal
- belts running in a vertical loop around each printed knob pulley
- printed standoff bracket holding the motor beside each knob

That is mechanically simpler than trying to stack the motors above or below the knobs.

## Suggested Initial CAD Targets

These are reasonable first-pass CAD assumptions from your measurements:

- `focus clamp pulley`
  - inner taper: match `37.52 mm` to `34.12 mm` over `26.5 mm`
  - split body: 2-piece clamp
  - wall thickness: start around `4-5 mm`
  - outer pulley OD: start around `48-60 mm`
- `X split-clamp pulley`
  - inner diameter near `27.8 mm`
  - outer pulley OD: start around `40-50 mm`
- `Y split-clamp pulley`
  - inner diameter near `32.93 mm`
  - outer pulley OD: start around `45-55 mm`

The final OD is not critical as long as:

- both pulleys are modeled accurately,
- your software knows the effective drive diameter or steps-per-revolution,
- the belt clears nearby microscope surfaces.

## Recommended Next Step

Before buying anything, measure:

- `X` and `Y` stage knob diameters
- center-to-center spacing of stage knobs
- free clearance around those knobs
- fine-focus knob diameter
- available mounting screws or clamp points on the stand

That measurement set is enough to start the CAD for the printed parts and to decide whether plain `NEMA 17` is sufficient or whether you should go directly to geared `NEMA 17` on `X/Y`.

## Notes On Sources

These are example purchase links and current references as of `April 13, 2026`. Prices and stock will move. For belts, pulleys, and generic CNC shields, the exact seller matters less than:

- correct bore
- correct belt pitch and width
- adequate motor torque
- reliable controller/driver supply

For the controller and drivers, prefer reputable vendors. For belts and pulleys, commodity sources are usually fine.
