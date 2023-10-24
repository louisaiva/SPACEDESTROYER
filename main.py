from viewerGL import ViewerGL
import glutils
from mesh import Mesh
from cpe3d import Object3D, Camera, Transformation3D, Text
import numpy as np
import OpenGL.GL as GL
import pyrr

FULLSCREEN = True

def main():


    
    
    # initialisation de la fenetre
    viewer = ViewerGL(FULLSCREEN)

    viewer.set_camera(Camera())
    viewer.cam.transformation.translation.y = 2
    viewer.cam.transformation.rotation_center = viewer.cam.transformation.translation.copy()

    # initialisation des shaders
    program3d_id = glutils.create_program_from_file('shaders/shader.vert', 'shaders/shader.frag')
    programGUI_id = glutils.create_program_from_file('shaders/gui.vert', 'shaders/gui.frag')
    
    # on charge la texture de la font
    font_texture = glutils.load_texture('ressources/fontB.jpg')
    
    # on passe les shaders & la texture a la fenetre
    viewer.init_program(program3d_id,programGUI_id,font_texture)
    
    

    viewer.run()


if __name__ == '__main__':
    main()