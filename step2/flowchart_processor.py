"""
Flowchart Image Processing Module
Author: Chethan S
Role: Flowchart Image Processing — shape detection, arrow detection, structure building.

This module accepts a flowchart image, processes it with OpenCV,
detects shapes (rectangles, diamonds, ovals, parallelograms) and arrows,
identifies connections between blocks, and outputs a structured flowchart
representation for the OCR + Logic module (Tanushri's module).
"""

import cv2
import numpy as np
import math
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Optional, Dict


# ---------------------------------------------------------------------------
# Data classes — the structured output handed to the next module
# ---------------------------------------------------------------------------

@dataclass
class FlowchartNode:
    """A single detected shape/block in the flowchart."""
    id: int
    shape: str          # "oval", "rectangle", "diamond", "parallelogram", "unknown"
    x: int              # top-left x of bounding rect
    y: int              # top-left y of bounding rect
    w: int              # width
    h: int              # height
    cx: int             # center x
    cy: int             # center y
    contour_points: list = field(default_factory=list)  # simplified contour vertices

    def __repr__(self):
        return f"Node(id={self.id}, shape={self.shape}, center=({self.cx},{self.cy}), size={self.w}x{self.h})"


@dataclass
class FlowchartEdge:
    """A directed connection between two nodes."""
    source_id: int
    target_id: int
    label: str = ""     # e.g. "Yes" / "No" for decision branches (filled by OCR)

    def __repr__(self):
        return f"Edge({self.source_id} -> {self.target_id})"


@dataclass
class FlowchartStructure:
    """Complete flowchart structure — nodes + edges."""
    nodes: List[FlowchartNode] = field(default_factory=list)
    edges: List[FlowchartEdge] = field(default_factory=list)
    image_width: int = 0
    image_height: int = 0

    def to_dict(self) -> dict:
        """Serialize to a plain dict for JSON export or handoff."""
        return {
            "image_width": self.image_width,
            "image_height": self.image_height,
            "nodes": [asdict(n) for n in self.nodes],
            "edges": [{"source_id": e.source_id,
                        "target_id": e.target_id,
                        "label": e.label} for e in self.edges],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def summary(self) -> str:
        lines = [f"Flowchart: {len(self.nodes)} nodes, {len(self.edges)} edges"]
        for n in self.nodes:
            lines.append(f"  {n}")
        for e in self.edges:
            lines.append(f"  {e}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Image pre-processing
# ---------------------------------------------------------------------------

class ImagePreprocessor:
    """Cleans up the input image for reliable contour detection."""

    @staticmethod
    def load_image(path: str) -> np.ndarray:
        """Load an image from disk. Raises FileNotFoundError if missing."""
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Image not found: {path}")
        img = cv2.imread(path)
        if img is None:
            raise ValueError(f"Could not decode image: {path}")
        return img

    @staticmethod
    def resize_if_needed(img: np.ndarray, max_dim: int = 1500) -> np.ndarray:
        """Resize large images so processing stays fast."""
        h, w = img.shape[:2]
        if max(h, w) <= max_dim:
            return img
        scale = max_dim / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    @staticmethod
    def to_binary(img: np.ndarray) -> np.ndarray:
        """Convert to a clean binary image (white shapes on black background)."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Adaptive threshold handles uneven lighting better than global
        binary = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=11,
            C=5,
        )

        # Morphological close to fill small gaps in shape outlines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Thin out the lines slightly so touching shapes/arrows separate
        # Use an open operation with a small kernel to break thin bridges
        thin_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, thin_kernel, iterations=1)

        return binary

    @classmethod
    def preprocess(cls, path: str) -> Tuple[np.ndarray, np.ndarray]:
        """Full pipeline: load → resize → binarize. Returns (original, binary)."""
        img = cls.load_image(path)
        img = cls.resize_if_needed(img)
        binary = cls.to_binary(img)
        return img, binary


# ---------------------------------------------------------------------------
# Shape detection
# ---------------------------------------------------------------------------

class ShapeDetector:
    """Detects and classifies flowchart shapes from contours."""

    # Minimum area (in pixels²) to consider — filters out noise
    MIN_AREA = 800
    # Maximum area ratio relative to image — filters out the page border
    MAX_AREA_RATIO = 0.60
"""
Flowchart Image Processing Module
Author: Chethan S
Role: Flowchart Image Processing — shape detection, arrow detection, structure building.

This module accepts a flowchart image, processes it with OpenCV,
detects shapes (rectangles, diamonds, ovals, parallelograms) and arrows,
identifies connections between blocks, and outputs a structured flowchart
representation for the OCR + Logic module (Tanushri's module).
"""

import cv2
import numpy as np
import math
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Optional, Dict


# ---------------------------------------------------------------------------
# Data classes — the structured output handed to the next module
# ---------------------------------------------------------------------------

@dataclass
class FlowchartNode:
    """A single detected shape/block in the flowchart."""
    id: int
    shape: str          # "oval", "rectangle", "diamond", "parallelogram", "unknown"
    x: int              # top-left x of bounding rect
    y: int              # top-left y of bounding rect
    w: int              # width
    h: int              # height
    cx: int             # center x
    cy: int             # center y
    contour_points: list = field(default_factory=list)  # simplified contour vertices

    def __repr__(self):
        return f"Node(id={self.id}, shape={self.shape}, center=({self.cx},{self.cy}), size={self.w}x{self.h})"


@dataclass
class FlowchartEdge:
    """A directed connection between two nodes."""
    source_id: int
    target_id: int
    label: str = ""     # e.g. "Yes" / "No" for decision branches (filled by OCR)

    def __repr__(self):
        return f"Edge({self.source_id} -> {self.target_id})"


@dataclass
class FlowchartStructure:
    """Complete flowchart structure — nodes + edges."""
    nodes: List[FlowchartNode] = field(default_factory=list)
    edges: List[FlowchartEdge] = field(default_factory=list)
    image_width: int = 0
    image_height: int = 0

    def to_dict(self) -> dict:
        """Serialize to a plain dict for JSON export or handoff."""
        return {
            "image_width": self.image_width,
            "image_height": self.image_height,
            "nodes": [asdict(n) for n in self.nodes],
            "edges": [{"source_id": e.source_id,
                        "target_id": e.target_id,
                        "label": e.label} for e in self.edges],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def summary(self) -> str:
        lines = [f"Flowchart: {len(self.nodes)} nodes, {len(self.edges)} edges"]
        for n in self.nodes:
            lines.append(f"  {n}")
        for e in self.edges:
            lines.append(f"  {e}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Image pre-processing
# ---------------------------------------------------------------------------

class ImagePreprocessor:
    """Cleans up the input image for reliable contour detection."""

    @staticmethod
    def load_image(path: str) -> np.ndarray:
        """Load an image from disk. Raises FileNotFoundError if missing."""
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Image not found: {path}")
        img = cv2.imread(path)
        if img is None:
            raise ValueError(f"Could not decode image: {path}")
        return img

    @staticmethod
    def resize_if_needed(img: np.ndarray, max_dim: int = 1500) -> np.ndarray:
        """Resize large images so processing stays fast."""
        h, w = img.shape[:2]
        if max(h, w) <= max_dim:
            return img
        scale = max_dim / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    @staticmethod
    def to_binary(img: np.ndarray) -> np.ndarray:
        """Convert to a clean binary image (white shapes on black background)."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Adaptive threshold handles uneven lighting better than global
        binary = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=11,
            C=5,
        )

        # Morphological close to fill small gaps in shape outlines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Thin out the lines slightly so touching shapes/arrows separate
        # Use an open operation with a small kernel to break thin bridges
        thin_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, thin_kernel, iterations=1)

        return binary

    @classmethod
    def preprocess(cls, path: str) -> Tuple[np.ndarray, np.ndarray]:
        """Full pipeline: load → resize → binarize. Returns (original, binary)."""
        img = cls.load_image(path)
        img = cls.resize_if_needed(img)
        binary = cls.to_binary(img)
        return img, binary


# ---------------------------------------------------------------------------
# Shape detection
# ---------------------------------------------------------------------------

class ShapeDetector:
    """Detects and classifies flowchart shapes from contours."""

    # Minimum area (in pixels²) to consider — filters out noise
    MIN_AREA = 800
    # Maximum area ratio relative to image — filters out the page border
    MAX_AREA_RATIO = 0.60

    @classmethod
    def find_shapes(cls, binary: np.ndarray) -> List[FlowchartNode]:
        """Find all shape contours and classify them."""
        # RETR_EXTERNAL loses individual blocks when arrows touch/connect them.
        # RETR_LIST returns all contours, allowing the actual shape contours to
        # be recovered even when a vertical arrow line creates one large outer
        # connected contour around the whole flowchart.
        contours, _ = cv2.findContours(
            binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE,
        )

        image_area = binary.shape[0] * binary.shape[1]
        nodes: List[FlowchartNode] = []
        node_id = 0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < cls.MIN_AREA:
                continue
            if area > cls.MAX_AREA_RATIO * image_area:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            cx, cy = x + w // 2, y + h // 2

            # Approximate the contour to reduce vertices
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.03 * peri, True)

            shape = cls._classify(cnt, approx, w, h)

            node = FlowchartNode(
                id=node_id,
                shape=shape,
                x=x, y=y, w=w, h=h,
                cx=cx, cy=cy,
                contour_points=approx.reshape(-1, 2).tolist(),
            )
            nodes.append(node)
            node_id += 1

        # Remove nodes that are fully contained inside another (nested contours)
        nodes = cls._remove_nested(nodes)

        # Re-assign IDs after filtering
        for i, node in enumerate(nodes):
            node.id = i

        return nodes

    @classmethod
    def _classify(cls, contour, approx, w: int, h: int) -> str:
        """Classify a shape based on its geometry."""
        num_vertices = len(approx)
        aspect_ratio = float(w) / h if h != 0 else 0
        area = cv2.contourArea(contour)
        rect_area = w * h
        extent = area / rect_area if rect_area != 0 else 0  # how much of bounding rect is filled

        # --- Oval / Ellipse / Rounded rectangle (Start/End) ---
        # High vertex count + high extent ≈ ellipse
        if num_vertices >= 6 and extent > 0.70:
            # Fit an ellipse and check how well it matches
            if len(contour) >= 5:
                ellipse = cv2.fitEllipse(contour)
                # Draw the fitted ellipse on a blank mask and compare
                mask_cnt = np.zeros((h + 40, w + 40), dtype=np.uint8)
                mask_ell = np.zeros_like(mask_cnt)
                shifted_cnt = contour - [max(0, int(cv2.boundingRect(contour)[0]) - 20),
                                          max(0, int(cv2.boundingRect(contour)[1]) - 20)]
                cv2.drawContours(mask_cnt, [shifted_cnt], -1, 255, -1)
                shifted_center = (int(ellipse[0][0]) - cv2.boundingRect(contour)[0] + 20,
                                  int(ellipse[0][1]) - cv2.boundingRect(contour)[1] + 20)
                cv2.ellipse(mask_ell, (shifted_center, ellipse[1], ellipse[2]), 255, -1)
                intersection = cv2.bitwise_and(mask_cnt, mask_ell)
                union = cv2.bitwise_or(mask_cnt, mask_ell)
                iou = cv2.countNonZero(intersection) / max(cv2.countNonZero(union), 1)
                if iou > 0.75:
                    return "oval"

        # --- Diamond (Decision) ---
        if num_vertices == 4:
            # A diamond has its 4 vertices near the midpoints of bounding-rect edges
            pts = approx.reshape(4, 2)
            cx_bb, cy_bb = w / 2, h / 2
            # Check if vertices are roughly at top, bottom, left, right of center
            dists_to_center = [math.hypot(p[0] - (pts[:, 0].min() + cx_bb),
                                           p[1] - (pts[:, 1].min() + cy_bb)) for p in pts]
            avg_dist = sum(dists_to_center) / 4
            spread = max(dists_to_center) - min(dists_to_center)
            # For a diamond the 4 corner distances are roughly equal
            if spread / max(avg_dist, 1) < 0.45 and extent < 0.78:
                return "diamond"

            # Also classify as diamond if the contour extent is typical of a rotated square
            if 0.45 < extent < 0.78 and 0.6 < aspect_ratio < 1.7:
                return "diamond"

        # --- Parallelogram (Input/Output) ---
        if num_vertices == 4:
            pts = approx.reshape(4, 2)
            # Sort by y, then by x to get top-left, top-right, bottom-right, bottom-left
            sorted_pts = cls._order_quadrilateral(pts)
            if sorted_pts is not None:
                tl, tr, br, bl = sorted_pts
                # A parallelogram has a noticeable horizontal skew
                top_skew = abs((tr[0] - tl[0]) - (br[0] - bl[0]))
                left_skew = abs(tl[0] - bl[0])
                right_skew = abs(tr[0] - br[0])
                # If opposite sides are roughly parallel but there is a skew
                if (left_skew > w * 0.08 or right_skew > w * 0.08) and extent > 0.70:
                    return "parallelogram"

        # --- Rectangle (Process) ---
        if num_vertices == 4 and extent > 0.80:
            return "rectangle"

        # Fallback: rectangles with slightly more vertices (rounded corners detected)
        if 4 <= num_vertices <= 6 and extent > 0.80 and 0.4 < aspect_ratio < 4.0:
            return "rectangle"

        # High-vertex-count shapes that aren't ellipses → likely rounded rectangles
        if num_vertices > 6 and extent > 0.80:
            return "rectangle"

        # Fallback for shapes merged with arrows — use aspect ratio & extent heuristics
        if extent > 0.60:
            # Tall/wide with many vertices: likely a shape that merged with an arrow
            if 0.3 < aspect_ratio < 3.5:
                # Circularity check: 4π·area / perimeter²  (1.0 = perfect circle)
                peri = cv2.arcLength(contour, True)
                circularity = (4 * math.pi * area) / (peri * peri) if peri > 0 else 0
                if circularity > 0.55:
                    return "oval"
                if extent > 0.80:
                    return "rectangle"

        return "unknown"

    @staticmethod
    def _order_quadrilateral(pts: np.ndarray) -> Optional[Tuple]:
        """Order 4 points as: top-left, top-right, bottom-right, bottom-left."""
        if len(pts) != 4:
            return None
        s = pts.sum(axis=1)
        d = np.diff(pts, axis=1).flatten()
        tl = pts[np.argmin(s)]
        br = pts[np.argmax(s)]
        tr = pts[np.argmin(d)]
        bl = pts[np.argmax(d)]
        return tl, tr, br, bl

    @staticmethod
    def _remove_nested(nodes: List[FlowchartNode]) -> List[FlowchartNode]:
        """
        Remove duplicate/nested shape contours without allowing a large
        connected arrow contour to hide real blocks.

        With RETR_LIST, a flowchart whose arrows touch the blocks can produce
        one large contour around the connected drawing. That contour is often
        classified as "unknown". It must NOT be allowed to remove smaller
        valid shape contours simply because their bounding boxes are nested
        inside it.

        Known shape contours can still suppress smaller duplicate contours.
        """
        to_remove = set()
        valid_shapes = {"oval", "rectangle", "diamond", "parallelogram"}

        for i, a in enumerate(nodes):
            for j, b in enumerate(nodes):
                if i == j or i in to_remove or j in to_remove:
                    continue

                # Check if 'a' is fully inside 'b'.
                a_inside_b = (
                    a.x >= b.x and a.y >= b.y and
                    a.x + a.w <= b.x + b.w and
                    a.y + a.h <= b.y + b.h
                )
                if not a_inside_b:
                    continue

                area_a = a.w * a.h
                area_b = b.w * b.h

                # Never let an unknown outer/connected contour remove a valid
                # flowchart block. This is the important RETR_LIST fix.
                if b.shape == "unknown" and a.shape in valid_shapes:
                 to_remove.add(j)
                 continue

                # If the outer contour is itself a recognized shape, it is
                # safe to treat the smaller nested contour as a duplicate.
                if b.shape in valid_shapes and area_a < area_b:
                    to_remove.add(i)
                    continue

                # Symmetric case: b is the smaller nested contour.
                if a.shape in valid_shapes and b.shape == "unknown":
                    continue

                if area_b < area_a and a.shape in valid_shapes:
                    to_remove.add(j)

        return [n for i, n in enumerate(nodes) if i not in to_remove]


# ---------------------------------------------------------------------------
# Arrow / line detection
# ---------------------------------------------------------------------------

class ArrowDetector:
    """Detects arrows/lines that connect shapes."""

    @classmethod
    def find_edges(cls, binary: np.ndarray, nodes: List[FlowchartNode]) -> List[FlowchartEdge]:
        """Detect connections between nodes using line detection + proximity."""
        if len(nodes) < 2:
            return []

        # Build a mask with shapes removed so only lines/arrows remain
        line_mask = cls._extract_lines(binary, nodes)

        # Detect line segments using the Hough transform
        edges = cls._detect_connections(line_mask, nodes)

        # Fallback: if Hough found very few edges, use proximity-based ordering
        if len(edges) < len(nodes) - 1:
            edges = cls._proximity_fallback(nodes, edges)

        # De-duplicate edges
        edges = cls._deduplicate(edges)

        return edges

    @staticmethod
    def _extract_lines(binary: np.ndarray, nodes: List[FlowchartNode]) -> np.ndarray:
        """Mask out the detected shapes, leaving only lines and arrows."""
        mask = binary.copy()
        for node in nodes:
            # Blank out the shape regions with a margin
            margin = 5
            x1 = max(0, node.x - margin)
            y1 = max(0, node.y - margin)
            x2 = min(mask.shape[1], node.x + node.w + margin)
            y2 = min(mask.shape[0], node.y + node.h + margin)
            mask[y1:y2, x1:x2] = 0
        return mask

    @classmethod
    def _detect_connections(cls, line_mask: np.ndarray,
                            nodes: List[FlowchartNode]) -> List[FlowchartEdge]:
        """Use HoughLinesP to detect line segments, then match endpoints to nodes."""
        edges: List[FlowchartEdge] = []

        # Dilate lines slightly so broken segments merge
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(line_mask, kernel, iterations=1)

        lines = cv2.HoughLinesP(
            dilated,
            rho=1,
            theta=np.pi / 180,
            threshold=30,
            minLineLength=15,
            maxLineGap=20,
        )

        if lines is None:
            return edges

        for line in lines:
            x1, y1, x2, y2 = line.flatten()
            src = cls._closest_node(x1, y1, nodes, max_dist=100)
            tgt = cls._closest_node(x2, y2, nodes, max_dist=100)

            if src is not None and tgt is not None and src != tgt:
                # Determine direction (top→bottom by default in flowcharts)
                src_node = nodes[src]
                tgt_node = nodes[tgt]
                # If the line endpoint (x1,y1) is closer to src and (x2,y2) to tgt
                # use that order; otherwise check vertical position
                if src_node.cy > tgt_node.cy:
                    src, tgt = tgt, src
                edges.append(FlowchartEdge(source_id=src, target_id=tgt))

        return edges

    @staticmethod
    def _closest_node(px: int, py: int, nodes: List[FlowchartNode],
                      max_dist: float) -> Optional[int]:
        """Find the nearest node to a point, within max_dist."""
        best_id = None
        best_dist = max_dist
        for node in nodes:
            # Distance from point to the edge of the node's bounding box
            dx = max(node.x - px, 0, px - (node.x + node.w))
            dy = max(node.y - py, 0, py - (node.y + node.h))
            dist = math.hypot(dx, dy)
            if dist < best_dist:
                best_dist = dist
                best_id = node.id
        return best_id

    @classmethod
    def _proximity_fallback(cls, nodes: List[FlowchartNode],
                            existing: List[FlowchartEdge]) -> List[FlowchartEdge]:
        """
        Fallback: connect nodes top-to-bottom by vertical proximity.
        Standard flowcharts flow downward, so sorting by Y gives a good default.
        Only adds edges that don't already exist.
        """
        existing_pairs = {(e.source_id, e.target_id) for e in existing}
        edges = list(existing)

        # Sort nodes top-to-bottom (by cy)
        sorted_nodes = sorted(nodes, key=lambda n: n.cy)

        for i in range(len(sorted_nodes) - 1):
            src = sorted_nodes[i]
            tgt = sorted_nodes[i + 1]
            pair = (src.id, tgt.id)
            reverse_pair = (tgt.id, src.id)
            if pair not in existing_pairs and reverse_pair not in existing_pairs:
                edges.append(FlowchartEdge(source_id=src.id, target_id=tgt.id))
                existing_pairs.add(pair)

        return edges

    @staticmethod
    def _deduplicate(edges: List[FlowchartEdge]) -> List[FlowchartEdge]:
        """Remove duplicate edges."""
        seen = set()
        unique = []
        for e in edges:
            key = (e.source_id, e.target_id)
            if key not in seen:
                seen.add(key)
                unique.append(e)
        return unique


# ---------------------------------------------------------------------------
# Visualization — debug helper to verify detection
# ---------------------------------------------------------------------------

class Visualizer:
    """Draw detected shapes and edges on the image for visual verification."""

    SHAPE_COLORS = {
        "oval": (0, 200, 0),          # green
        "rectangle": (200, 0, 0),     # blue
        "diamond": (0, 0, 200),       # red
        "parallelogram": (200, 200, 0),  # cyan
        "unknown": (128, 128, 128),   # gray
    }

    @classmethod
    def draw(cls, img: np.ndarray, structure: FlowchartStructure) -> np.ndarray:
        """Draw nodes and edges on a copy of the image."""
        canvas = img.copy()

        # Draw edges first (so shapes appear on top)
        for edge in structure.edges:
            src = next((n for n in structure.nodes if n.id == edge.source_id), None)
            tgt = next((n for n in structure.nodes if n.id == edge.target_id), None)
            if src and tgt:
                cv2.arrowedLine(
                    canvas,
                    (src.cx, src.cy), (tgt.cx, tgt.cy),
                    color=(0, 165, 255), thickness=2, tipLength=0.03,
                )

        # Draw shapes
        for node in structure.nodes:
            color = cls.SHAPE_COLORS.get(node.shape, (128, 128, 128))
            pts = np.array(node.contour_points, dtype=np.int32)
            if len(pts) >= 3:
                cv2.drawContours(canvas, [pts], -1, color, 2)

            # Label
            label = f"#{node.id} {node.shape}"
            cv2.putText(
                canvas, label,
                (node.x, max(node.y - 8, 15)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA,
            )

        return canvas


# ---------------------------------------------------------------------------
# Main processor — public API
# ---------------------------------------------------------------------------

class FlowchartProcessor:
    """
    Top-level API for Chethan's module.

    Usage:
        processor = FlowchartProcessor()
        structure = processor.process("flowchart.png")
        print(structure.summary())
        print(structure.to_json())
    """

    def __init__(self, debug: bool = False, output_dir: str = ""):
        self.debug = debug
        self.output_dir = output_dir

    def process(self, image_path: str) -> FlowchartStructure:
        """
        Full pipeline: image → preprocessed → shapes → arrows → structure.

        Parameters:
            image_path: Path to the flowchart image file.

        Returns:
            FlowchartStructure with detected nodes and edges.
        """
        # Step 1 — Preprocess
        img, binary = ImagePreprocessor.preprocess(image_path)
        h, w = img.shape[:2]

        if self.debug:
            self._save_debug("01_binary.png", binary)

        # Step 2 — Detect shapes
        nodes = ShapeDetector.find_shapes(binary)

        if self.debug:
            print(f"[DEBUG] Detected {len(nodes)} shapes")
            for n in nodes:
                print(f"  {n}")

        # Step 3 — Detect arrows / edges
        edges = ArrowDetector.find_edges(binary, nodes)

        if self.debug:
            print(f"[DEBUG] Detected {len(edges)} edges")
            for e in edges:
                print(f"  {e}")

        # Build structure
        structure = FlowchartStructure(
            nodes=nodes,
            edges=edges,
            image_width=w,
            image_height=h,
        )

        # Step 4 — Save debug visualization
        if self.debug:
            annotated = Visualizer.draw(img, structure)
            self._save_debug("02_detected.png", annotated)
            self._save_debug_json("03_structure.json", structure.to_dict())

        return structure

    def process_and_visualize(self, image_path: str, output_path: str = "") -> FlowchartStructure:
        """Process and save an annotated image regardless of debug flag."""
        img, binary = ImagePreprocessor.preprocess(image_path)
        nodes = ShapeDetector.find_shapes(binary)
        edges = ArrowDetector.find_edges(binary, nodes)

        structure = FlowchartStructure(
            nodes=nodes, edges=edges,
            image_width=img.shape[1], image_height=img.shape[0],
        )

        annotated = Visualizer.draw(img, structure)
        if not output_path:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_detected{ext}"
        cv2.imwrite(output_path, annotated)
        print(f"Annotated image saved to: {output_path}")

        return structure

    # -- helpers --

    def _save_debug(self, filename: str, img: np.ndarray):
        out_dir = self.output_dir or "debug_output"
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, filename)
        cv2.imwrite(path, img)
        print(f"[DEBUG] Saved {path}")

    def _save_debug_json(self, filename: str, data: dict):
        out_dir = self.output_dir or "debug_output"
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"[DEBUG] Saved {path}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    """Command-line entry point for quick testing."""
    if len(sys.argv) < 2:
        print("Usage: python flowchart_processor.py <image_path> [--debug]")
        print("  <image_path>  Path to a flowchart image (PNG, JPG, etc.)")
        print("  --debug       Save intermediate images and print details")
        sys.exit(1)

    image_path = sys.argv[1]
    debug = "--debug" in sys.argv

    processor = FlowchartProcessor(debug=debug)
    try:
        structure = processor.process(image_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print(structure.summary())
    print("=" * 50)
    print("\nJSON output:")
    print(structure.to_json())


if __name__ == "__main__":
    main()

  
  
# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    """Command-line entry point for quick testing."""
    if len(sys.argv) < 2:
        print("Usage: python flowchart_processor.py <image_path> [--debug]")
        print("  <image_path>  Path to a flowchart image (PNG, JPG, etc.)")
        print("  --debug       Save intermediate images and print details")
        sys.exit(1)

    image_path = sys.argv[1]
    debug = "--debug" in sys.argv

    processor = FlowchartProcessor(debug=debug)
    try:
        structure = processor.process(image_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print(structure.summary())
    print("=" * 50)
    print("\nJSON output:")
    print(structure.to_json())


if __name__ == "__main__":
    main()
