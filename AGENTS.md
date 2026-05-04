# Ducky Printer Project - Agent Notes

## Print Dimensions (Citizen CT-S310II USB Printer)

### Image Print Defaults
- **Target width**: 8.0 cm (576 px)
- **Target height**: 17.3 cm (1245 px)
- **Total print length**: ~18.0 cm (17.3cm image + ~0.7cm printer cut overhead)
- **Resolution**: 72 pixels per cm
- **Rotation**: 90° clockwise (images print horizontally / landscape)
- **Scaling**: Forced resize to exact target (distortion allowed to fill area)

### Image Processing Pipeline
1. Load original image (e.g. 2127 x 946 px)
2. Rotate 90° clockwise → 946 x 2127 px
3. Trim white borders → 942 x 2123 px (varies by image)
4. Force resize to 576 x 1245 px (fills full print area)
5. Print with `bitImageColumn` implementation, `center=False`
6. Full paper cut

### Printer Hardware Notes
- **Model**: Citizen CT-S310IIEBK (USB class 7)
- **Paper width**: 80mm
- **Print width**: 576 dots/line (72mm effective)
- **Cut overhead**: ~0.7cm added to print length by the cut mechanism
- **USB endpoints**: in_ep=0x81, out_ep=0x02
- **ESC/POS init**: `ESC @` (reset) + `ESC 3 0` (line spacing = 0)
