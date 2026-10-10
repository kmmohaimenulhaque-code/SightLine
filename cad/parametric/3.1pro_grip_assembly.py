import os
from build123d import *

EXPORT_DIR = "../exports"

def make_chassis():
    with BuildPart() as chassis:
        # Core block 30x150x40mm (X, Y, Z)
        Box(30, 150, 40)
        
        # 3-2-1 Locating Pins on top face (Z = 20)
        with BuildSketch(chassis.faces().sort_by(Axis.Z)[-1]):
            with Locations((0, 50)):
                Circle(1.5)
            with Locations((10, -50), (-10, -50)):
                Circle(1.0)
        extrude(amount=8)
        
        # T-slot on bottom face for ballast (Z = -20)
        with BuildSketch(chassis.faces().sort_by(Axis.Z)[0]):
            with Locations((0, 0)):
                Rectangle(12, 150)
        extrude(amount=-5, mode=Mode.SUBTRACT)
        
        with BuildSketch(Plane.XY.offset(-15)):
             with Locations((0,0)):
                 Rectangle(20, 150)
        extrude(amount=-10, mode=Mode.SUBTRACT)

        # Basic ergonomic grip handle extending down
        with BuildSketch(Plane.YZ):
            with Locations((0, -20)):
                 Polygon([(0,0), (-20, -100), (30, -120), (40, 0)])
        extrude(amount=15, both=True)

    return chassis.part

def make_adapter():
    with BuildPart() as adapter:
        Box(80, 160, 10)
        
        with BuildSketch(adapter.faces().sort_by(Axis.Z)[0]):
            with Locations((0, 50)):
                Circle(1.575)
            with Locations((10, -50), (-10, -50)):
                Circle(1.075)
        extrude(amount=-9, mode=Mode.SUBTRACT)

        with BuildSketch(adapter.faces().sort_by(Axis.Z)[-1]):
            Rectangle(77.5, 160.5)
        extrude(amount=6, mode=Mode.SUBTRACT)

        with BuildSketch(adapter.faces().sort_by(Axis.Z)[-1]):
            with Locations((-20, 55)):
                 Rectangle(40, 45)
        extrude(amount=-10, mode=Mode.SUBTRACT)
        
    return adapter.part

def make_ballast_slider():
    with BuildPart() as slider:
        Box(19.7, 40, 9.7)
        with Locations((0, 0, 5)):
             Box(11.7, 40, 5)
        
        with Locations((0, 0, 12)):
             Box(30, 40, 5)
             
        with BuildSketch(Plane.XY.offset(14.5)):
             Circle(1.6)
        extrude(amount=-30, mode=Mode.SUBTRACT)

    return slider.part

if __name__ == "__main__":
    export_path = os.path.join(os.path.dirname(__file__), EXPORT_DIR)
    os.makedirs(export_path, exist_ok=True)
    
    chassis = make_chassis()
    adapter = make_adapter()
    slider = make_ballast_slider()
    
    print("Exporting parts to STEP and STL...")
    
    try:
        export_step(chassis, os.path.join(export_path, "3.1pro_chassis.step"))
        export_stl(chassis, os.path.join(export_path, "3.1pro_chassis.stl"))
        
        export_step(adapter, os.path.join(export_path, "3.1pro_adapter.step"))
        export_stl(adapter, os.path.join(export_path, "3.1pro_adapter.stl"))
        
        export_step(slider, os.path.join(export_path, "3.1pro_ballast_slider.step"))
        export_stl(slider, os.path.join(export_path, "3.1pro_ballast_slider.stl"))
        print("Export successful.")
    except Exception as e:
        print(f"Export failed: {e}")
