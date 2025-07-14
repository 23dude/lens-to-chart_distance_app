# app.py

import streamlit as st
import math

# --- Page config ---
st.set_page_config(
    page_title="Multi-Camera Testing Distance Range Calculator",
    layout="wide"
)

st.title("Multi-Camera Testing Distance Range Calculator")
st.warning(
    "⚠️ Follow distance/field width guidelines for inkjet charts. "
    "You may move closer with higher-quality photographic or chrome-on-glass charts, but for office(not recommended) or low-quality prints, keep the camera as far as possible."
)

# --- Sidebar inputs ---
st.sidebar.header("Environment & Chart Settings")
num_cameras = st.sidebar.number_input(
    "Number of cameras to test", min_value=1, step=1, value=3
)

# Chart size selection (width in mm)
chart_option = st.sidebar.selectbox(
    "Chart size",
    ("A4 (210×297 mm)", "Letter (216×279 mm)", "Legal (216×356 mm)",
     "A3 (297×420 mm)", "Ledger (279×432 mm)")
)
chart_width_mm_map = {
    "A4 (210×297 mm)": 210.0,
    "Letter (216×279 mm)": 216.0,
    "Legal (216×356 mm)": 216.0,
    "A3 (297×420 mm)": 297.0,
    "Ledger (279×432 mm)": 279.0
}
chart_width_cm = chart_width_mm_map[chart_option] / 10.0

wall_width_cm = st.sidebar.number_input(
    "Wall width (cm)", min_value=1.0, value=300.0
)
max_room_dist_cm = st.sidebar.number_input(
    "Max Allowable Distance from Wall (cm) – Based on Room Size", min_value=1.0, value=200.0
)
min_chart_fraction = st.sidebar.slider(
    "Min chart fraction of HFOV", min_value=0.0, max_value=1.0, step=0.05, value=0.1
)

PIXELS_PER_CM = 55  # threshold for no sensor falloff

# --- Collect camera specs and compute ranges ---
cameras = []

st.header("Camera Specifications")
for i in range(num_cameras):
    st.subheader(f"Camera #{i+1}")
    name = st.text_input(f"Name for Camera #{i+1}", value=f"Camera {i+1}", key=f"name_{i}")
    h_pixels = st.number_input(f"Horizontal resolution (px)", min_value=1, value=3848, key=f"hpx_{i}")
    v_pixels = st.number_input(f"Vertical resolution (px)", min_value=1, value=2160, key=f"vpx_{i}")
    # Sensor width vs pixel size
    sensor_mode = st.radio(
        "Define sensor by", ("Sensor Width (mm)", "Pixel Size (µm)"),
        key=f"sensor_mode_{i}", horizontal=True
    )
    if sensor_mode == "Sensor Width (mm)":
        sensor_width_mm = st.number_input("Sensor width (mm)", min_value=0.0, value=7.696, key=f"sw_{i}")
        pixel_size_um = (sensor_width_mm / h_pixels) * 1000.0
        st.write(f"→ pixel size: **{pixel_size_um:.2f} µm**")
    else:
        pixel_size_um = st.number_input("Pixel size (µm)", min_value=0.0, value=2.0, key=f"ps_{i}")
        sensor_width_mm = (h_pixels * pixel_size_um) / 1000.0
        st.write(f"→ sensor width: **{sensor_width_mm:.2f} mm**")

    # always compute sensor height & diagonal
    sensor_height_mm = (v_pixels * pixel_size_um) / 1000.0
    sensor_diag_mm = math.hypot(sensor_width_mm, sensor_height_mm)

    # Focal length vs diagonal FOV
    lens_mode = st.radio(
        "Define lens by", ("Focal Length (mm)", "Diagonal FOV (°)"),
        key=f"lens_mode_{i}", horizontal=True
    )
    if lens_mode == "Focal Length (mm)":
        focal_length_mm = st.number_input("Focal length (mm)", min_value=0.0, value=3.0, key=f"fl_{i}")
        dfov_deg = math.degrees(2 * math.atan((sensor_diag_mm / 2) / focal_length_mm)) if focal_length_mm else 0
        st.write(f"→ Diagonal FOV: **{dfov_deg:.1f}°**")
    else:
        dfov_deg = st.number_input("Diagonal FOV (°)", min_value=0.0, value=72.0, key=f"dfov_{i}")
        focal_length_mm = (sensor_diag_mm / 2) / math.tan(math.radians(dfov_deg / 2)) if dfov_deg else 0
        st.write(f"→ focal length: **{focal_length_mm:.2f} mm**")

    # Minimum HFOV & distance
    hfov_min_cm = h_pixels / PIXELS_PER_CM
    hfov_min_mm = hfov_min_cm * 10
    mag_min = sensor_width_mm / hfov_min_mm if hfov_min_mm else 0
    min_dist_mm = focal_length_mm / mag_min + focal_length_mm if mag_min else 0

    # Maximum HFOV & distance (chart + wall + room)
    hfov_max_chart_cm = chart_width_cm / min_chart_fraction if min_chart_fraction else float("inf")
    hfov_max_cm = min(wall_width_cm, hfov_max_chart_cm)
    hfov_max_mm = hfov_max_cm * 10
    mag_max = sensor_width_mm / hfov_max_mm if hfov_max_mm else 0
    max_dist_mm = focal_length_mm / mag_max + focal_length_mm if mag_max else 0
    max_dist_mm = min(max_dist_mm, max_room_dist_cm * 10)

    cameras.append({"name": name, "min_mm": min_dist_mm, "max_mm": max_dist_mm})

# --- Intersection calculation ---
lower_mm = max(cam["min_mm"] for cam in cameras)
upper_mm = min(cam["max_mm"] for cam in cameras)

# --- Display results ---
st.header("Results")
for cam in cameras:
    st.write(f"**{cam['name']}**: {cam['min_mm']/10:.1f} cm to {cam['max_mm']/10:.1f} cm")

if lower_mm <= upper_mm:
    st.success(f"🔍 Common distance range: {lower_mm/10:.1f} cm to {upper_mm/10:.1f} cm")
else:
    st.error("⚠️ No overlapping range found. Adjust specs or environment.")

st.info("Distances use a simplified magnification formula; treat results as approximate.")
