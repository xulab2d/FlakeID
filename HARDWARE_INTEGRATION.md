# Hardware Integration

## MVP path

The MVP is designed to ship before camera and stage models are finalized.

- `flakefinder.hardware.mock_adapter.MockHardware`: folder-backed simulation for development and testing.
- `flakefinder.hardware.micromanager_adapter.MicroManagerHardware`: preferred integration path for a motorized glovebox microscope when devices are reachable through Micro-Manager.
- `flakefinder.hardware.vendor_stub.VendorSDKStub`: reserved for cases where Micro-Manager is not viable and direct SDK work is required.

## Micro-Manager path

Use Micro-Manager when:

- the camera is supported through a stable device adapter,
- stage and focus devices can be driven from MMCore,
- the lab wants one control surface for acquisition.

Current implementation:

- lazy imports `pycro-manager`
- exposes camera snap, stage moves, focus moves, illumination/exposure hooks
- leaves exact device property names as TODOs because the hardware stack is still unknown

## Vendor SDK path

Use the vendor stub when:

- the camera cannot be controlled reliably through Micro-Manager,
- performance or feature access requires the native SDK,
- glovebox deployment needs a simpler direct integration.

## Hardware-specific TODOs

- confirm camera vendor/model and pixel format output
- confirm stage controller coordinate units and travel limits
- confirm focus actuator units and autofocus availability
- map illumination channels and property names
- validate exposure/gain property names in Micro-Manager
- calibrate objective-specific field of view and pixel size
- capture dark frames and flat fields per configuration
