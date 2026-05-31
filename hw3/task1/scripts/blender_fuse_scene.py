"""Compose Task 1 meshes and render a Blender walkthrough video."""

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def resolve_asset(asset):
    if "path" in asset:
        path = PROJECT_ROOT / asset["path"]
        if path.exists():
            return path
        raise FileNotFoundError(path)
    matches = sorted(PROJECT_ROOT.glob(asset["glob"]))
    if not matches:
        raise FileNotFoundError(f"No files match {asset['glob']}")
    return matches[-1]


def add_vertex_color_material(obj):
    if obj.type != "MESH" or obj.data.materials:
        return
    if not obj.data.color_attributes:
        return
    color_attribute = obj.data.color_attributes[0]
    material = bpy.data.materials.new(name=f"{obj.name}-vertex-color")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    principled = nodes.get("Principled BSDF")
    vertex_color = nodes.new(type="ShaderNodeVertexColor")
    vertex_color.layer_name = color_attribute.name
    links.new(vertex_color.outputs["Color"], principled.inputs["Base Color"])
    obj.data.materials.append(material)


def import_mesh(path):
    before = set(bpy.context.scene.objects)
    suffix = path.suffix.lower()
    if suffix == ".ply":
        bpy.ops.wm.ply_import(filepath=str(path))
    elif suffix == ".obj":
        bpy.ops.wm.obj_import(filepath=str(path))
    elif suffix in {".glb", ".gltf"}:
        bpy.ops.import_scene.gltf(filepath=str(path))
    else:
        raise ValueError(f"Unsupported mesh format: {path}")
    return [obj for obj in bpy.context.scene.objects if obj not in before]


def configure_asset(asset):
    path = resolve_asset(asset)
    objects = import_mesh(path)
    for obj in objects:
        obj.name = f"{asset['name']}-{obj.name}"
        obj.location = asset["location"]
        obj.rotation_euler = [math.radians(value) for value in asset["rotation_deg"]]
        obj.scale = asset["scale"]
        add_vertex_color_material(obj)
    print(f"Imported {asset['name']}: {path}")


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def add_camera_animation(scene, config):
    camera_data = bpy.data.cameras.new("WalkthroughCamera")
    camera = bpy.data.objects.new("WalkthroughCamera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    target = config["target"]
    radius = config["radius"]
    height = config["height"]
    for frame in range(1, scene.frame_end + 1):
        angle = 2.0 * math.pi * (frame - 1) / scene.frame_end
        camera.location = [
            target[0] + radius * math.cos(angle),
            target[1] + radius * math.sin(angle),
            height,
        ]
        look_at(camera, target)
        camera.keyframe_insert(data_path="location", frame=frame)
        camera.keyframe_insert(data_path="rotation_euler", frame=frame)


def add_lighting(scene):
    scene.world.color = (0.08, 0.08, 0.08)
    sun_data = bpy.data.lights.new(name="Sun", type="SUN")
    sun_data.energy = 2.0
    sun = bpy.data.objects.new(name="Sun", object_data=sun_data)
    sun.rotation_euler = (math.radians(35), math.radians(-20), math.radians(25))
    scene.collection.objects.link(sun)

    area_data = bpy.data.lights.new(name="Fill", type="AREA")
    area_data.energy = 1200
    area_data.shape = "DISK"
    area_data.size = 5.0
    area = bpy.data.objects.new(name="Fill", object_data=area_data)
    area.location = (0.0, 0.0, 6.0)
    scene.collection.objects.link(area)


def main():
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    scene = bpy.context.scene
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    for asset in config["assets"]:
        configure_asset(asset)

    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = config["resolution_x"]
    scene.render.resolution_y = config["resolution_y"]
    scene.render.resolution_percentage = 100
    scene.render.fps = config["fps"]
    scene.frame_start = 1
    scene.frame_end = config["frames"]
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"

    output_video = PROJECT_ROOT / config["output_video"]
    output_blend = PROJECT_ROOT / config["output_blend"]
    output_video.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(output_video)

    add_lighting(scene)
    add_camera_animation(scene, config["camera"])
    bpy.ops.wm.save_as_mainfile(filepath=str(output_blend))
    bpy.ops.render.render(animation=True)
    print(f"Rendered walkthrough: {output_video}")


if __name__ == "__main__":
    main()
