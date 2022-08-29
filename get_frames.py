import bpy
import json
import os
import sys
import requests
import sys
argv = sys.argv
argv = argv[argv.index("--") + 1:]  # get all args after "--"

task_id = argv[0]

scene = bpy.context.scene
frames = scene.frame_end - scene.frame_start + 1


data = {}


def exists(lib):
    if lib.packed_file is None:  # it's an external file
        path = lib.filepath
        if path.startswith('//'):
            path = path[2:]
        if path != '' and not os.path.exists(os.path.join(os.path.dirname(os.environ['BLEND_FILE']).encode('utf-8'),  bpy.path.abspath(path).encode('utf-8'))):
            return False
    return True


def list_missing_files():
    ret = []
    for lib in bpy.data.libraries:
        try:
            if exists(lib) == False:
                ret.append(lib.filepath)
        except:
            pass
    for lib in bpy.data.images:
        try:
            if exists(lib) == False:
                ret.append(lib.filepath)
        except:
            pass
    return ret


def has_active_file_output_node(activeScenes: list):
    for scene in activeScenes:
        if not scene.use_nodes:
            continue

        for node in scene.node_tree.nodes:
            if node.mute:
                continue
            if type(node) == bpy.types.CompositorNodeOutputFile or node.type == 'OUTPUT_FILE':
                return True
    return False


def has_GPencil_object():
    for ob in bpy.data.objects:
        if ob.type == 'GPENCIL':
            return True
    return False


def can_use_tile():
    """
    check if tiling can be used

    returns False when:
        - denoising is used
        - compositing is used
        - node tree is enabled and contains nodes
    returns True otherwise
    """
    # in Blender 2.9x they moved
    # 		scene.view_layers['RenderLayer'].cycles.use_denoising
    # 	to
    #		scene.cycles.use_denoising
    try:
        if bpy.context.scene.cycles.use_denoising:
            return False
    except AttributeError:
        for layer in bpy.context.scene.view_layers:
            if layer.cycles.use_denoising:
                return False

    if not bpy.context.scene.render.use_compositing:
        return True

    if bpy.context.scene.use_nodes:
        if (bpy.context.scene.node_tree != None or
                bpy.context.scene.node_tree.nodes != None) and \
                len(bpy.context.scene.node_tree.nodes.items()) > 0:
            return False

    return True


def get_engine():
    """
    check which engine is being used for scenes, that are actually in use

    @return 1 engine name or 'MIXED' when multiple engines are in use at the same time
    @return 2 list of scenes actually in use
    """

    _eng = bpy.context.scene.render.engine

    # check if composition is enabled in the main scene
    if bpy.context.scene.use_nodes:
        # select all scenes with active users and render layers
        _scn = list()
        active_scenes = list()

        for scene in bpy.data.scenes:
            if scene.users > 0 and any(l.use for l in scene.view_layers):
                _scn.append(scene)

        # select only scenes, which are actually in use in the compositor
        for node in bpy.context.scene.node_tree.nodes:
            if node.type == "R_LAYERS":
                if node.scene in _scn:
                    active_scenes.append(node.scene)

        # check if all use the same render engine
        if active_scenes:  # this is empty, when use_nodes is True, but the compositor does not contain any nodes
            _eng = active_scenes[0].render.engine
        else:
            return _eng, [bpy.context.scene]

        if all(s.render.engine == _eng for s in active_scenes):
            return _eng, active_scenes
        else:
            return "MIXED", active_scenes
    else:
        return _eng, [bpy.context.scene]


def get_samples(scenes: list):
    """returns the number of samples of the scene with the highest number"""
    _samples = list()

    for scene in scenes:
        _samples.append(scene.cycles.samples)

    return max(_samples)


def optix_is_active(scenes: list):
    """
    checks if any of the used scenes uses Optix Denoising

    !! We have to check "the other way round", because scene.cycles.denoiser is only "OPTIX" on a machine with Nvidia GPU
        otherwise it will return just an empty string ("")
    """

    try:
        for scene in scenes:
            if scene.render.engine == 'CYCLES':
                if scene.cycles.use_denoising:
                    if scene.cycles.denoiser not in ['NLM', 'OPENIMAGEDENOISE']:
                        return True
    except:
        pass

    return False


def total_samples(scenes: list):
    """returns the total number of samples for the scene with the highest number"""

    _samples = list()

    for scene in scenes:
        _s = scene.render.resolution_x * scene.render.resolution_y
        _s *= float(scene.render.resolution_percentage) / 100.0
        _s *= float(scene.render.resolution_percentage) / 100.0
        _s *= get_samples([scene])

        _samples.append(_s)

    return max(_samples)


def list_scripted_driver():
    for o in bpy.data.objects:
        if o.animation_data is not None:
            for driver in o.animation_data.drivers:
                if driver.driver is not None and driver.driver.type == 'SCRIPTED':
                    return True
    return False


def get_resolution_x():
    if bpy.context.scene.render.use_multiview and bpy.context.scene.render.image_settings.views_format == 'STEREO_3D':
        if bpy.context.scene.render.image_settings.stereo_3d_format.display_mode == 'TOPBOTTOM':
            return bpy.context.scene.render.resolution_x
        elif bpy.context.scene.render.image_settings.stereo_3d_format.display_mode == 'SIDEBYSIDE':
            return bpy.context.scene.render.resolution_x * 2
        elif bpy.context.scene.render.image_settings.stereo_3d_format.display_mode == 'INTERLACE':
            return bpy.context.scene.render.resolution_x
        elif bpy.context.scene.render.image_settings.stereo_3d_format.display_mode == 'ANAGLYPH':
            return bpy.context.scene.render.resolution_x
        else:
            return bpy.context.scene.render.resolution_x
    else:
        return bpy.context.scene.render.resolution_x


def get_resolution_y():
    if bpy.context.scene.render.use_multiview and bpy.context.scene.render.image_settings.views_format == 'STEREO_3D':
        if bpy.context.scene.render.image_settings.stereo_3d_format.display_mode == 'TOPBOTTOM':
            return bpy.context.scene.render.resolution_y * 2
        elif bpy.context.scene.render.image_settings.stereo_3d_format.display_mode == 'SIDEBYSIDE':
            return bpy.context.scene.render.resolution_y
        elif bpy.context.scene.render.image_settings.stereo_3d_format.display_mode == 'INTERLACE':
            return bpy.context.scene.render.resolution_y
        elif bpy.context.scene.render.image_settings.stereo_3d_format.display_mode == 'ANAGLYPH':
            return bpy.context.scene.render.resolution_y
        else:
            return bpy.context.scene.render.resolution_y
    else:
        return bpy.context.scene.render.resolution_y


def use_adaptive_sampling():
    return bpy.context.scene.cycles.use_adaptive_sampling


# retrieves enabled passes by checking a render layers node outputs
def get_enabled_passes_by_node(scene: bpy.types.Scene):
    passes = []
    renderlayers_node = None
    has_renderlayers_node = False
    is_nodes_enabled = scene.use_nodes
    scene.use_nodes = True  # needs to be enabled for scene.node_tree.nodes to be initialized
    nodes = scene.node_tree.nodes

    for node in nodes:
        if node.type == 'R_LAYERS':
            has_renderlayers_node = True
            renderlayers_node = node
            break

    if has_renderlayers_node is False:
        renderlayers_node = nodes.new('CompositorNodeRLayers')

    for rpass in renderlayers_node.outputs:
        if rpass.enabled is True:
            passes.append(rpass)

    if has_renderlayers_node is False:
        nodes.remove(renderlayers_node)

    scene.use_nodes = is_nodes_enabled

    return passes

# retrieves enabled passes by checking (not enabling) the passes checkboxes in the layers properties
# the three expected possible inputs are viewlayer, viewlayer.eevee, viewlayer.cycles


def get_enabled_passes_by_settings(settings_object):
    passes = []

    for item in dir(settings_object):
        if item.startswith("use_pass_") and getattr(settings_object, item):
            if item != "use_pass_cryptomatte_accurate":
                passes.append(item)

    return passes


def find_disable_passses(passes_settings, scene):
    # gets the enabled passes as shown in a render layers node
    actual_passes = get_enabled_passes_by_node(scene)
    enabled_toggles = get_enabled_passes_by_settings(passes_settings)
    need_to_disable = []

    for toggle in enabled_toggles:
        setattr(passes_settings, toggle, False)
        updated_passes = get_enabled_passes_by_node(scene)
        if len(actual_passes) == len(updated_passes):
            if toggle != "use_pass_combined":
                need_to_disable.append(toggle)
        setattr(passes_settings, toggle, True)

    return need_to_disable


def get_passes(scene: bpy.types.Scene, viewlayer: bpy.types.ViewLayer, engine: str):
    """retrieves two lists of passes:
       first list: passes that are enabled and will be rendered
       second list: passes that are enabled but cannot be rendered by the engine, therefor need to be disabled by the user
    """
    # engine specific passes remain enabled in Blender even when switching between engines
    disable_common_passes = find_disable_passses(viewlayer, scene)
    engine_specific_settings = None
    if engine == 'BLENDER_EEVEE':
        engine_specific_settings = viewlayer.eevee
    elif engine == 'CYCLES':
        engine_specific_settings = viewlayer.cycles

    disable_engine_specific_passes = find_disable_passses(
        engine_specific_settings, scene)

    need_to_disable = disable_common_passes + disable_engine_specific_passes

    # gets the enabled passes as shown in a render layers node
    actual_passes = get_enabled_passes_by_node(scene)

    passes = []
    for rpass in actual_passes:
        passes.append(rpass.name)

    return passes, need_to_disable


render_engine, active_scenes = get_engine()


info = {}
info['version'] = str(bpy.data.version[0]) + "." + str(bpy.data.version[1])
info['scene'] = str(bpy.context.scene.name)
info['start_frame'] = str(bpy.context.scene.frame_start)
info['end_frame'] = str(bpy.context.scene.frame_end)
info['total_frames'] = frames
info['output_file_extension'] = str(bpy.context.scene.render.file_extension)
info['output_file_format'] = str(
    bpy.context.scene.render.image_settings.file_format)
info['engine'] = str(render_engine)
info['optix_is_active'] = optix_is_active(active_scenes)
info['resolution_percentage'] = str(
    bpy.context.scene.render.resolution_percentage)
info['resolution_x'] = str(get_resolution_x())
info['resolution_y'] = str(get_resolution_y())
info['framerate'] = str(bpy.context.scene.render.fps /
                        bpy.context.scene.render.fps_base)
info['can_use_tile'] = str(can_use_tile())
info['missing_files'] = list_missing_files()
info['have_camera'] = bpy.context.scene.camera != None
info['scripted_driver'] = str(list_scripted_driver())
info['has_active_file_output_node'] = has_active_file_output_node(
    active_scenes)
info['has_GPencil_object'] = has_GPencil_object()
info['use_adaptive_sampling'] = use_adaptive_sampling()

enabled_passes, disable_passes = get_passes(
    bpy.context.scene, bpy.context.view_layer, str(render_engine))
info['enabled_passes'] = enabled_passes
info['must_be_disabled_passes'] = disable_passes
info['exr_codec'] = str(bpy.context.scene.render.image_settings.exr_codec)

if info['engine'] == 'CYCLES':
    info['cycles_samples'] = str(total_samples(active_scenes))
    info['cycles_pixel_samples'] = str(get_samples(active_scenes))

r = requests.post("http://backend:8002/v1/",
                  files=dict(id=task_id, data=json.dumps(info)))
