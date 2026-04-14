# Microscope Scan Intake

When you finish scanning the Zeiss Axio, place the files here:

- `zeiss_axio_cad/scan_input/`

Recommended contents:

- one full-microscope mesh or point cloud
- one close scan of the `X/Y` knob region
- one close scan of the focus knob region
- any photos showing proposed cable and motor routing

Preferred formats:

- `OBJ`
- `PLY`
- `STL`
- `GLB` or `GLTF`

Also include one short note with:

- scan app used
- any scale/reference object present in the scan
- whether the scale was already calibrated
- which side you want the electronics/controller mounted on

The first design pass after the scan will be:

1. import scan references,
2. confirm knob centers and clearances,
3. design motor bracket envelopes,
4. update pulley offsets,
5. add first chassis parts.
