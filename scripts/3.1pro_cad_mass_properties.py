#!/usr/bin/env python3
import os
import json
import argparse
import math

class SightlineMassSolver:
    def __init__(self, target_mass=1060, target_com_x=50, target_com_z=15):
        self.target_mass = target_mass
        self.target_com_x = target_com_x
        self.target_com_z = target_com_z
        
        # Component masses in grams
        self.components = {
            'chassis': {'mass': 280, 'com_x': 0, 'com_y': 0, 'com_z': 0},
            'grip': {'mass': 120, 'com_x': -20, 'com_y': 0, 'com_z': -50},
            'adapter': {'mass': 45, 'com_x': 0, 'com_y': 0, 'com_z': 25}
        }
        
        # Will be loaded from JSON
        self.phone_mass = 0
        self.phone_com_z = 35 # approx center of phone
        
    def load_phone_profile(self, filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
            self.phone_mass = data.get('mass_g', 200)
            print(f"Loaded phone {data.get('model')} with mass {self.phone_mass}g")
            
    def solve_ballast(self):
        current_mass = sum(c['mass'] for c in self.components.values()) + self.phone_mass
        mass_deficit = self.target_mass - current_mass
        
        if mass_deficit <= 0:
            print("WARNING: System is already over target mass!")
            return None
            
        print(f"Required ballast mass: {mass_deficit}g")
        
        # Calculate current moment about X and Z
        moment_x = sum(c['mass'] * c['com_x'] for c in self.components.values())
        moment_z = sum(c['mass'] * c['com_z'] for c in self.components.values()) + (self.phone_mass * self.phone_com_z)
        
        # Target moments
        target_moment_x = self.target_mass * self.target_com_x
        target_moment_z = self.target_mass * self.target_com_z
        
        # Required ballast position
        ballast_x = (target_moment_x - moment_x) / mass_deficit
        ballast_z = (target_moment_z - moment_z) / mass_deficit
        
        return {
            'ballast_mass_g': mass_deficit,
            'ballast_pos_x_mm': ballast_x,
            'ballast_pos_z_mm': ballast_z
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SIGHTLINE Mass Properties Solver")
    parser.append = parser.add_argument
    parser.append('--phone-profile', type=str, required=True, help="Path to phone profile JSON")
    args = parser.parse_args()
    
    solver = SightlineMassSolver()
    solver.load_phone_profile(args.phone_profile)
    result = solver.solve_ballast()
    
    if result:
        print("\n--- Solver Results ---")
        print(f"Ballast Mass to Add: {result['ballast_mass_g']:.1f} g")
        print(f"Place Ballast at X: {result['ballast_pos_x_mm']:.1f} mm")
        print(f"Place Ballast at Z: {result['ballast_pos_z_mm']:.1f} mm")
        print("----------------------\n")
