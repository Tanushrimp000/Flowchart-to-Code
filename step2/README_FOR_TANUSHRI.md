# Chethan's Module → Tanushri's Module

## What I Built

I built the **Flowchart Image Processing** module. It takes a flowchart image and detects all the shapes (ovals, rectangles, diamonds, parallelograms) and the connections (arrows) between them.

**Your job starts where mine ends** — you take my output and run OCR to extract text from each shape.

---

## How to Use My Module

### Install dependencies
```bash
pip install opencv-python numpy
```

### Basic usage
```python
from flowchart_processor import FlowchartProcessor

processor = FlowchartProcessor()
structure = processor.process("flowchart.png")
```

---

## What You Get From My Module

A `FlowchartStructure` object with **nodes** (shapes) and **edges** (connections).

### Each Node has:
| Field     | What it means                          |
|-----------|----------------------------------------|
| `id`      | Unique number (0, 1, 2...)             |
| `shape`   | `"oval"` / `"rectangle"` / `"diamond"` / `"parallelogram"` |
| `x, y`    | Top-left corner of the shape           |
| `w, h`    | Width and height of the shape          |
| `cx, cy`  | Center point of the shape              |

### Each Edge has:
| Field       | What it means              |
|-------------|----------------------------|
| `source_id` | Node ID where arrow starts |
| `target_id` | Node ID where arrow ends   |

### Shape → Flowchart meaning:
- **oval** = Start / End
- **rectangle** = Process
- **diamond** = Decision (if-else)
- **parallelogram** = Input / Output

---

## How to Extract Text (Your Part)

Use each node's `x, y, w, h` to crop that region from the original image, then run Tesseract OCR on it:

```python
import cv2
from flowchart_processor import FlowchartProcessor

# Step 1: Load image
image = cv2.imread("flowchart.png")

# Step 2: Get structure from my module
processor = FlowchartProcessor()
structure = processor.process("flowchart.png")

# Step 3: For each shape, crop and run OCR (YOUR PART)
for node in structure.nodes:
    cropped = image[node.y : node.y + node.h, node.x : node.x + node.w]
    # Now pass 'cropped' to Tesseract OCR to extract text
    # text = pytesseract.image_to_string(cropped)
    print(f"Node #{node.id} | Shape: {node.shape} | Text: ...")

# Step 4: Use edges to know the flow order
for edge in structure.edges:
    print(f"Node {edge.source_id} → Node {edge.target_id}")
```

---

## JSON Output (if you prefer)

```python
print(structure.to_json())
```

```json
{
  "nodes": [
    {"id": 0, "shape": "oval", "x": 140, "y": 35, "w": 120, "h": 50, "cx": 200, "cy": 60},
    {"id": 1, "shape": "rectangle", "x": 130, "y": 190, "w": 140, "h": 60, "cx": 200, "cy": 220},
    {"id": 2, "shape": "oval", "x": 140, "y": 365, "w": 120, "h": 50, "cx": 200, "cy": 390}
  ],
  "edges": [
    {"source_id": 0, "target_id": 1},
    {"source_id": 1, "target_id": 2}
  ]
}
```

---

## Files I'm Sending You

| File | What it is |
|------|------------|
| `flowchart_processor.py` | My module — just import it |
| `requirements.txt` | Run `pip install -r requirements.txt` |
| `test_flowchart_processor.py` | My tests (28/28 passing) — optional for you |

**You only need `flowchart_processor.py` and `requirements.txt`.**

---

## Quick Summary

```
Your input:  flowchart.png
     ↓
My module:   FlowchartProcessor.process("flowchart.png")
     ↓
My output:   List of shapes (with positions) + connections between them
     ↓
Your job:    Crop each shape → OCR → extract text → identify block types → build logic flow
```

Any questions, ping me! — Chethan
