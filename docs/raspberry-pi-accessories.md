# Raspberry Pi Accessories

Reference guide for official Raspberry Pi accessories. Source: https://www.raspberrypi.com/documentation/accessories/

---

## Cameras

### Camera Module 3
- **Sensor**: Sony IMX708, 12 megapixels
- **Variants**: Standard, NoIR (no infrared filter), Wide (102° FoV), Wide NoIR
- **Interface**: CSI (MIPI)
- **Focus**: Autofocus (PDAF)
- **Use cases**: Photography, video recording, computer vision

### HQ Camera
- **Sensor**: Sony IMX477, 12.3 megapixels
- **Interface**: CSI (MIPI)
- **Lens mount**: C/CS-mount (interchangeable lenses)
- **Use cases**: High-quality photography, machine vision, industrial imaging

### Global Shutter Camera
- **Sensor**: Sony IMX296, 1.58 megapixels
- **Interface**: CSI (MIPI)
- **Shutter**: Global (no rolling shutter distortion)
- **Use cases**: High-speed motion capture, barcode scanning, robotics

### AI Camera
- **Sensor**: Sony IMX500, 12.3 megapixels
- **Special feature**: On-chip NPU (Neural Processing Unit)
- **Interface**: CSI (MIPI)
- **Use cases**: Real-time AI inference at the edge, object detection, pose estimation
- **Key benefit**: Offloads AI processing from the CPU/GPU directly to the sensor

---

## Displays

### Touch Display (Original)
- **Size**: 7 inches
- **Resolution**: 800 × 480 pixels
- **Interface**: DSI (Display Serial Interface)
- **Touch**: Capacitive 10-finger touch
- **Compatible**: Raspberry Pi B+ and later

### Touch Display 2
- **Size**: 7 inches
- **Resolution**: 800 × 480 pixels
- **Interface**: DSI
- **Touch**: Capacitive 10-finger touch
- **Improvements**: Better brightness, updated connector design
- **Compatible**: Raspberry Pi B+ and later
- **Use cases**: Tablets, info dashboards, kiosks, entertainment systems

---

## HAT Accessories

HATs (Hardware Attached on Top) connect to the 40-pin GPIO header.

### Sense HAT
- **Sensors**: Accelerometer, gyroscope, magnetometer, temperature, humidity, barometric pressure, colour/light
- **Display**: 8×8 RGB LED matrix
- **Input**: 5-way joystick
- **Use cases**: Environmental monitoring, orientation sensing, education (used on the ISS)
- **Python library**: `sense_hat`

### Build HAT
- **Purpose**: Control LEGO® Technic™ motors and sensors
- **Ports**: 4× LEGO connector ports
- **Power**: Requires 8V barrel jack power supply
- **Library**: `buildhat` Python library
- **Use cases**: LEGO robotics, STEM education, creative engineering projects

### TV HAT
- **Function**: Receive DVB-T2 digital TV signals
- **Interface**: USB (via HAT form factor)
- **Connector**: Coaxial (F-type)
- **Use cases**: Live TV streaming over a home network, PVR/DVR projects

### AI HAT+
- **Accelerator**: Hailo NPU (13 TOPS or 26 TOPS variants)
- **Interface**: PCIe (via Raspberry Pi 5's M.2 connector)
- **Use cases**: Real-time AI inference, vision models, YOLOv5/v8, object detection
- **Compatible**: Raspberry Pi 5 only
- **Note**: System auto-detects and offloads supported AI workloads to NPU

### M.2 HAT+
- **Purpose**: Attach NVMe SSDs to Raspberry Pi 5
- **Interface**: PCIe Gen 2 ×1 (via Raspberry Pi 5's M.2 slot)
- **Supported form factors**: M.2 2230, 2242
- **Use cases**: High-speed storage, boot from NVMe, media servers
- **Compatible**: Raspberry Pi 5 only

---

## Debug & Development

### Debug Probe
- **Function**: USB to SWD (Serial Wire Debug) and UART bridge
- **Use cases**: Debugging Raspberry Pi Pico / RP2040 projects, serial console access
- **Interface**: USB-C (host side), 3-pin JST SH (SWD/UART)
- **Software**: Works with OpenOCD

---

## Keyboard & Mouse

### Official Raspberry Pi Keyboard
- **Layout**: Available in multiple regional layouts
- **Interface**: USB (built-in hub with 2× USB-A ports)
- **Feature**: Built-in USB hub allows connecting mouse and other peripherals

### Official Raspberry Pi Mouse
- **Interface**: USB
- **Design**: Compact, matches keyboard colour scheme

---

## Compatibility Summary

| Accessory        | Pi 4 | Pi 5 | Pi Zero 2W | Pico |
|-----------------|------|------|------------|------|
| Camera Module 3 | ✓    | ✓    | ✓          | —    |
| HQ Camera       | ✓    | ✓    | ✓          | —    |
| Global Shutter  | ✓    | ✓    | ✓          | —    |
| AI Camera       | ✓    | ✓    | ✓          | —    |
| Touch Display 2 | ✓    | ✓    | —          | —    |
| Sense HAT       | ✓    | ✓    | ✓          | —    |
| Build HAT       | ✓    | ✓    | —          | —    |
| TV HAT          | ✓    | ✓    | —          | —    |
| AI HAT+         | —    | ✓    | —          | —    |
| M.2 HAT+        | —    | ✓    | —          | —    |
| Debug Probe     | —    | —    | —          | ✓    |

---

## Further Reading

- [Camera documentation](https://www.raspberrypi.com/documentation/accessories/camera.html)
- [AI Camera documentation](https://www.raspberrypi.com/documentation/accessories/ai-camera.html)
- [Touch Display 2 documentation](https://www.raspberrypi.com/documentation/accessories/touch-display-2.html)
- [Sense HAT documentation](https://www.raspberrypi.com/documentation/accessories/sense-hat.html)
- [Build HAT documentation](https://www.raspberrypi.com/documentation/accessories/build-hat.html)
- [AI HAT+ documentation](https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html)
- [M.2 HAT+ documentation](https://www.raspberrypi.com/documentation/accessories/m2-hat-plus.html)
- [TV HAT documentation](https://www.raspberrypi.com/documentation/accessories/tv-hat.html)
