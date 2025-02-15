import cv2
import numpy as np
import os
from pathlib import Path
import math

def hex_to_bgr(color_str: str):
    COLOR_NAME_TO_HEX = {
        "black": "#000000",
        "white": "#FFFFFF",
        "yellow": "#FFFF00",
        "red": "#FF0000",
        "blue": "#0000FF",
        "green": "#00FF00",
        "gray": "#808080",
        "grey": "#808080"
    }
    
    if not color_str.startswith('#'):
        color_str = COLOR_NAME_TO_HEX.get(color_str.lower())
        if color_str is None:
            raise ValueError(f"Color name '{color_str}' is not recognized.")
    
    color_str = color_str.lstrip('#')
    if len(color_str) != 6:
        raise ValueError("Invalid hex color format.")
    
    r = int(color_str[0:2], 16)
    g = int(color_str[2:4], 16)
    b = int(color_str[4:6], 16)
    return (b, g, r)

class VideoTextOverlayOpencv:
    def __init__(self, font=cv2.FONT_HERSHEY_SIMPLEX):
        self.font = font
        self.default_style = {
            'color': 'white',          
            'stroke_color': 'black',   
            'stroke_width': 2,         
            'size': 60,                
            'bg_color': None,          
            'bg_opacity': 0.4,
            'shadow': True,
            'shadow_color': '#000000',
            'shadow_offset': (2, 2)
        }
    
    def _draw_text(self, frame, text: str, style: dict, text_alpha: float = 1.0):
        overlay = frame.copy()
        h, w = frame.shape[:2]

        font_scale = style.get('size', 60) / 30.0
        thickness = style.get('stroke_width', 2)

        (text_width, text_height), baseline = cv2.getTextSize(text, self.font, font_scale, thickness)
        x = (w - text_width) // 2
        y = (h + text_height - baseline) // 2

        if style.get('bg_color'):
            padding = 20
            rect_x1 = max(x - padding, 0)
            rect_y1 = max(y - text_height - padding, 0)
            rect_x2 = min(x + text_width + padding, w)
            rect_y2 = min(y + padding, h)
            bg_color = hex_to_bgr(style['bg_color'])
            cv2.rectangle(overlay, (rect_x1, rect_y1), (rect_x2, rect_y2), bg_color, -1)
            overlay = cv2.addWeighted(overlay, style.get('bg_opacity', 0.4), frame, 1 - style['bg_opacity'], 0)
            frame = overlay.copy()
            overlay = frame.copy()

        stroke_color = hex_to_bgr(style['stroke_color'])
        text_color = hex_to_bgr(style['color'])
        
        if style.get('shadow', True):
            shadow_color = hex_to_bgr(style['shadow_color'])
            sx = x + style['shadow_offset'][0]
            sy = y + style['shadow_offset'][1]
            cv2.putText(overlay, text, (sx, sy), self.font, font_scale, shadow_color, thickness, cv2.LINE_AA)

        for dx in range(-thickness, thickness+1):
            for dy in range(-thickness, thickness+1):
                if dx == 0 and dy == 0: continue
                cv2.putText(overlay, text, (x+dx, y+dy), self.font, font_scale, stroke_color, thickness, cv2.LINE_AA)

        cv2.putText(overlay, text, (x, y), self.font, font_scale, text_color, thickness, cv2.LINE_AA)
        return cv2.addWeighted(overlay, text_alpha, frame, 1 - text_alpha, 0)

    def _get_video_duration(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"Error opening video: {video_path}")
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        return frame_count / fps

    def create_video(self, video_path: str, text: list, output_path: str, style: dict = None) -> str:
        current_style = self.default_style.copy()
        if style: current_style.update(style)
        
        text_segments = text
        total_text_duration = sum(d for _, d in text_segments)
        segments = []
        current_start = 0.0
        for t, d in text_segments:
            segments.append( (t, current_start, current_start + d) )
            current_start += d

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames_needed = int(total_text_duration * fps)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

        frame_idx = 0
        while frame_idx < total_frames_needed:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    break
            current_time = frame_idx / fps

            active_text = next( (t for t, s, e in segments if s <= current_time < e), None)
            if active_text:
                frame = self._draw_text(frame, active_text, current_style)
            
            out.write(frame)
            frame_idx += 1

        cap.release()
        out.release()
        return output_path

    def create_animated_video(self, video_path: str, text: list, output_path: str, style: dict = None, animation: str = 'fade') -> str:
        current_style = self.default_style.copy()
        if style: current_style.update(style)

        text_segments = text
        total_text_duration = sum(d for _, d in text_segments)
        segments = []
        current_start = 0.0
        for t, d in text_segments:
            segments.append( (t, current_start, current_start + d) )
            current_start += d

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames_needed = int(total_text_duration * fps)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))

        frame_idx = 0
        while frame_idx < total_frames_needed:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    break
            current_time = frame_idx / fps

            active_segment = next( ((t, s) for t, s, e in segments if s <= current_time < e), None)
            if active_segment:
                text_str, seg_start = active_segment
                t_anim = current_time - seg_start

                if animation == 'fade':
                    alpha = min(t_anim * 2, 1.0) if t_anim < 0.5 else max(1.0 - (t_anim - 0.5) * 2, 0.0)
                elif animation == 'slide':
                    y_offset = int(50 * (1 - min(t_anim, 1.0)))
                    frame = self._draw_text(frame, text_str, current_style)
                elif animation == 'pulse':
                    alpha = 0.7 + 0.3 * math.sin(2 * math.pi * t_anim)
                else:
                    alpha = 1.0

                frame = self._draw_text(frame, text_str, current_style, alpha if animation in ['fade', 'pulse'] else 1.0)

            out.write(frame)
            frame_idx += 1

        cap.release()
        out.release()
        return output_path

if __name__ == "__main__":
    overlay = VideoTextOverlayOpencv()

    # Static text with multiple segments
    overlay.create_video(
        video_path="iShowSpeed's Iconic Subway Surfers Clip.mp4",
        text=[("Welcome!", 2), ("Watch This", 3), ("Goodbye!", 1.5)],
        output_path="output/multi_sejgment.mp4",
        style={'color': 'yellow', 'bg_color': '#000000'}
    )

    # Animated text with fade effect
    overlay.create_animated_video(
        video_path="iShowSpeed's Iconic Subway Surfers Clip.mp4",
        text=[("Fade In", 2), ("Stay", 3), ("Fade Out", 2)],
        output_path="output/animated_fade.mp4",
        animation='pulse'
    )