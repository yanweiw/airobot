import pkgutil
import threading
import time
from numbers import Number

import pybullet as p
import pybullet_data

PB_CLIENT = None
STEP_SIM_MODE = True
RENDER = False
GRAVITY_CONST = -9.8


def load_pb(render=False):
    """
    Load the pybullet client

    Args:
        render (bool): if GUI should be used for rendering or not
    """
    global PB_CLIENT, RENDER, GRAVITY_CONST
    RENDER = render
    if render:
        PB_CLIENT = p.connect(p.GUI)
    else:
        PB_CLIENT = p.connect(p.DIRECT)
        # # using the eglRendererPlugin (hardware OpenGL acceleration)
        egl = pkgutil.get_loader('eglRenderer')
        if egl:
            p.loadPlugin(egl.get_filename(), "_eglRendererPlugin",
                         physicsClientId=PB_CLIENT)
        else:
            p.loadPlugin("eglRendererPlugin",
                         physicsClientId=PB_CLIENT)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, GRAVITY_CONST,
                 physicsClientId=PB_CLIENT)
    if not render:
        th_sim = threading.Thread(target=step_rt_simulation)
        th_sim.daemon = True
        th_sim.start()
    else:
        p.setRealTimeSimulation(1, physicsClientId=PB_CLIENT)


def step_rt_simulation():
    """
    Run step simulation all the time in backend
    """
    global STEP_SIM_MODE, PB_CLIENT
    while True:
        if not STEP_SIM_MODE:
            p.stepSimulation(physicsClientId=PB_CLIENT)
        time.sleep(0.001)


def set_step_sim(step_mode=True):
    """
    Turn on/off the realtime simulation mode

    Args:
        step_mode (bool): run the simulation in step mode if
            it is True. Otherwise, the simulation will be
            in realtime
    """
    global STEP_SIM_MODE
    STEP_SIM_MODE = step_mode
    if RENDER:
        if step_mode:
            p.setRealTimeSimulation(0, physicsClientId=PB_CLIENT)
        else:
            p.setRealTimeSimulation(1, physicsClientId=PB_CLIENT)


def load_urdf(filename, base_pos=None, base_ori=None, scaling=1.0, **kwargs):
    """
    Load URDF into the pybullet client

    Args:
        filename (str): a relative or absolute path to the URDF
            file on the file system of the physics server.
        base_pos (list or np.ndarray): create the base of the object
            at the specified position in world space coordinates [X,Y,Z].
            Note that this position is of the URDF link position.
        base_ori (list or np.ndarray): create the base of the object
            at the specified orientation as world space
            quaternion [X,Y,Z,W].
        scaling (float): apply a scale factor to the URDF model

    Returns:
        int: a body unique id, a non-negative integer value.
        If the URDF file cannot be loaded, this integer will
        be negative and not a valid body unique id.

    """
    if scaling <= 0:
        raise ValueError('Scaling should be a positive number.')
    if base_pos is None:
        base_pos = [0, 0, 0]
    if base_ori is None:
        base_ori = [0, 0, 0, 1]
    body_id = p.loadURDF(filename,
                         basePosition=base_pos,
                         baseOrientation=base_ori,
                         globalScaling=scaling,
                         physicsClientId=PB_CLIENT,
                         **kwargs)
    p.setGravity(0, 0, GRAVITY_CONST, physicsClientId=PB_CLIENT)
    return body_id


def load_sdf(filename, scaling=1.0, **kwargs):
    """
    Load SDF into the pybullet client

    Args:
        filename (str): a relative or absolute path to the SDF
            file on the file system of the physics server.
        scaling (float): apply a scale factor to the SDF model

    Returns:
        int: a body unique id, a non-negative integer value.
        If the SDF file cannot be loaded, this integer will
        be negative and not a valid body unique id.

    """
    if scaling <= 0:
        raise ValueError('Scaling should be a positive number.')
    body_id = p.loadSDF(filename,
                        globalScaling=scaling,
                        physicsClientId=PB_CLIENT,
                        **kwargs)
    p.setGravity(0, 0, GRAVITY_CONST, physicsClientId=PB_CLIENT)
    return body_id


def load_mjcf(filename, **kwargs):
    """
    Load SDF into the pybullet client

    Args:
        filename (str): a relative or absolute path to the MJCF
            file on the file system of the physics server.

    Returns:
        int: a body unique id, a non-negative integer value.
        If the MJCF file cannot be loaded, this integer will
        be negative and not a valid body unique id.

    """
    body_id = p.loadMJCF(filename,
                         physicsClientId=PB_CLIENT,
                         **kwargs)
    p.setGravity(0, 0, GRAVITY_CONST, physicsClientId=PB_CLIENT)
    return body_id


def load_geom(shape_type, size=None, mass=0.5, visualfile=None,
              collifile=None, mesh_scale=None, rgba=None,
              specular=None, shift_pos=None, shift_ori=None,
              base_pos=None, base_ori=None):
    """
    Load a regular geometry (`sphere`, `box`, `capsule`, `cylinder`, `mesh`)

    Note:
        Please do not call **load_geom('capsule')** when you are using
        **robotiq gripper**. The capsule generated will be in wrong size
        if the mimicing thread (_th_mimic_gripper) in the robotiq
        gripper class starts running.
        This might be a PyBullet Bug (current version is 2.5.6).
        Note that other geometries(box, sphere, cylinder, etc.)
        are not affected by the threading in the robotiq gripper.

    Args:
        shape_type (str): one of [`sphere`, `box`, `capsule`, `cylinder`,
            `mesh`]

        size (float or list): Defaults to None.

             If shape_type is sphere: size should be a float (radius).

             If shape_type is capsule or cylinder: size should be a 2-element
             list (radius, length).

             If shape_type is box: size can be a float (same edge length
             for 3 dims) or a 3-element list containing the size of 3 edges

             size doesn't take effect if shape_type is mesh.

        mass (float): mass of the object in kg

        visualfile (str): path to the visual mesh file.
            only needed when the shape_type is mesh. If it's None, same
            collision mesh file will be used as the visual mesh file.

        collifile (str): path to the collision mesh file.
            only needed when the shape_type is mesh. If it's None, same
            viusal mesh file will be used as the collision mesh file.

        mesh_scale (float or list): scale the mesh. If it's a float number,
            the mesh will be scaled in same ratio along 3 dimensions. If it's
            a list, then it should contain 3 elements (scales along 3 dimensions).
        rgba (list): color components for red, green, blue and alpha, each in
            range [0, 1] (shape: :math:`[4,]`)
        specular(list): specular reflection color components for red, green, blue
            and alpha, each in range [0, 1] (shape: :math:`[4,]`)
        shift_pos (list): translational offset of collision shape, visual shape,
            and inertial frame (shape: :math:`[3,]`)
        shift_ori (list): rotational offset (quaternion [x, y, z, w]) of collision shape,
            visual shape, and inertial frame (shape: :math:`[4,]`)
        base_pos (list): cartesian world position of the base (shape: :math:`[3,]`)
        base_ori (list): cartesian world orientation of the base as
            quaternion [x, y, z, w] (shape: :math:`[4,]`)

    Returns:
        int: a body unique id, a non-negative integer value or -1 for failure.

    """
    global GRAVITY_CONST
    pb_shape_types = {'sphere': p.GEOM_SPHERE,
                      'box': p.GEOM_BOX,
                      'capsule': p.GEOM_CAPSULE,
                      'cylinder': p.GEOM_CYLINDER,
                      'mesh': p.GEOM_MESH}
    if shape_type not in pb_shape_types.keys():
        raise TypeError('The following shape type is not '
                        'supported: %s' % shape_type)

    collision_args = {'shapeType': pb_shape_types[shape_type]}
    visual_args = {'shapeType': pb_shape_types[shape_type]}
    if shape_type == 'sphere':
        if size is not None and not (isinstance(size, float) and size > 0):
            raise TypeError('size should be a positive float number for a sphere.')
        collision_args['radius'] = 0.5 if size is None else size
        visual_args['radius'] = collision_args['radius']
    elif shape_type == 'box':
        if isinstance(size, float):
            size = [size, size, size]
        elif isinstance(size, list):
            if len(size) != 3:
                raise ValueError('If size is a list, its length'
                                 ' should be 3 for a box')
        elif size is not None:
            raise TypeError('size should be a float number, or a 3-element list '
                            'for a box')
        collision_args['halfExtents'] = [1, 1, 1] if size is None else size
        visual_args['halfExtents'] = collision_args['halfExtents']
    elif shape_type in ['capsule', 'cylinder']:
        if size is not None:
            if not isinstance(size, list) or len(size) != 2:
                raise TypeError('size should be a 2-element list (radius, length)'
                                'for a capsule or a cylinder.')
            for si in size:
                if not isinstance(si, Number) or si <= 0.0:
                    raise TypeError('size should be a list that contains 2 positive'
                                    'numbers (radius, length) for a capsule or '
                                    'a cylinder.')
        collision_args['radius'] = 0.5 if size is None else size[0]
        visual_args['radius'] = collision_args['radius']
        collision_args['height'] = 1.0 if size is None else size[1]
        visual_args['length'] = collision_args['height']
    elif shape_type == 'mesh':
        if visualfile is None and collifile is None:
            raise ValueError('At least one of the visualfile and collifile'
                             'should be provided!')
        if visualfile is None:
            visualfile = collifile
        elif collifile is None:
            collifile = visualfile
        if not isinstance(visualfile, str):
            raise TypeError('visualfile should be the path to '
                            'the visual mesh file!')
        if not isinstance(collifile, str):
            raise TypeError('collifile should be the path to '
                            'the collision mesh file!')
        collision_args['fileName'] = collifile
        visual_args['fileName'] = visualfile
        if isinstance(mesh_scale, float):
            mesh_scale = [mesh_scale, mesh_scale, mesh_scale]
        elif isinstance(mesh_scale, list):
            if len(mesh_scale) != 3:
                raise ValueError('If mesh_scale is a list, its length'
                                 ' should be 3.')
        elif mesh_scale is not None:
            raise TypeError('mesh_scale should be a float number, or a 3-element list.')
        collision_args['meshScale'] = [1, 1, 1] if mesh_scale is None else mesh_scale
        visual_args['meshScale'] = collision_args['meshScale']
    else:
        raise TypeError('The following shape type is not '
                        'supported: %s' % shape_type)

    visual_args['rgbaColor'] = rgba
    visual_args['specularColor'] = specular
    collision_args['collisionFramePosition'] = shift_pos
    collision_args['collisionFrameOrientation'] = shift_ori
    visual_args['visualFramePosition'] = shift_pos
    visual_args['visualFrameOrientation'] = shift_ori

    collision_args['physicsClientId'] = PB_CLIENT
    visual_args['physicsClientId'] = PB_CLIENT

    p.configureDebugVisualizer(p.COV_ENABLE_RENDERING, 0,
                               physicsClientId=PB_CLIENT)
    vs_id = p.createVisualShape(**visual_args)
    cs_id = p.createCollisionShape(**collision_args)
    body_id = p.createMultiBody(baseMass=mass,
                                baseInertialFramePosition=shift_pos,
                                baseInertialFrameOrientation=shift_ori,
                                baseCollisionShapeIndex=cs_id,
                                baseVisualShapeIndex=vs_id,
                                basePosition=base_pos,
                                baseOrientation=base_ori,
                                physicsClientId=PB_CLIENT)
    p.configureDebugVisualizer(p.COV_ENABLE_RENDERING, 1,
                               physicsClientId=PB_CLIENT)
    p.setGravity(0, 0, GRAVITY_CONST, physicsClientId=PB_CLIENT)
    return body_id