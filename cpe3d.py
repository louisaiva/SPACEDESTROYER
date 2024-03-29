import OpenGL.GL as GL
import pyrr
import numpy as np 
import math

class Transformation3D: 
    def __init__(self, euler = pyrr.euler.create(), center = pyrr.Vector3(), translation = pyrr.Vector3()):
        self.rotation_euler = euler.copy()
        self.rotation_center = center.copy()
        self.translation = translation.copy()

class Object:
    def __init__(self, vao, nb_triangle, program, texture):
        self.vao = vao
        self.nb_triangle = nb_triangle
        self.program = program
        self.texture = texture
        self.visible = True

    def draw(self):
        if self.visible : 
            GL.glUseProgram(self.program)
            GL.glBindVertexArray(self.vao)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
            GL.glDrawElements(GL.GL_TRIANGLES, 3*self.nb_triangle, GL.GL_UNSIGNED_INT, None)

class Object3D(Object):
    def __init__(self, vao, nb_triangle, program, texture, transformation, fixed = False):
        super().__init__(vao, nb_triangle, program, texture)
        self.transformation = transformation
        self.fixed = fixed
        if self.fixed:
            self.rot = pyrr.matrix44.create_from_eulers(self.transformation.rotation_euler)

    def draw(self):
        GL.glUseProgram(self.program)

        # Récupère l'identifiant de la variable pour le programme courant
        loc = GL.glGetUniformLocation(self.program, "translation_model")
        # Vérifie que la variable existe
        if (loc == -1) :
            print("Pas de variable uniforme : translation_model")
        # Modifie la variable pour le programme courant
        translation = self.transformation.translation
        GL.glUniform4f(loc, translation.x, translation.y, translation.z, 0)

        # Récupère l'identifiant de la variable pour le programme courant
        loc = GL.glGetUniformLocation(self.program, "rotation_center_model")
        # Vérifie que la variable existe
        if (loc == -1) :
            print("Pas de variable uniforme : rotation_center_model")
        # Modifie la variable pour le programme courant
        rotation_center = self.transformation.rotation_center
        GL.glUniform4f(loc, rotation_center.x, rotation_center.y, rotation_center.z, 0)

        if not self.fixed :
            self.rot = pyrr.matrix44.create_from_eulers(self.transformation.rotation_euler)
        loc = GL.glGetUniformLocation(self.program, "rotation_model")
        if (loc == -1) :
            print("Pas de variable uniforme : rotation_model")
        GL.glUniformMatrix4fv(loc, 1, GL.GL_FALSE, self.rot)

        super().draw()

    def set_transformation(self, transformation):
        self.transformation = transformation

    def rotate_to_dir(self,direction,ancre=-math.pi/2):
        
        # tourne l'objet dans la direction
        # direction est un vecteur possédant 2 composantes : une en X et une autre en Z
        
        # calcul des coordonnées
        # dx = cat.transformation.translation[0] - self.transformation.translation[0]
        # dz = cat.transformation.translation[2] - self.transformation.translation[2]
        
        # print("rotate obj to",direction)
        
        # initialisation
        dx,dz = direction
        
        # calcul de l'angle
        hyp = math.sqrt(dx**2 + dz**2)
        angle = math.acos(dx/hyp)
        
        # inversion de l'angle dans la moitié gauche du repère
        if dz < 0:
            angle = -angle
        
        # calcul de l'ancre de rotation
        # ancre = -math.pi/2

        # on applique la rotation
        self.transformation.rotation_euler[pyrr.euler.index.yaw] = angle + ancre

    def move_to_dir(self,direc,speed):
        
        # fait avancer l'obj dans la direction voulue à une vitesse de speed/frame
        
        dx,dz = direc
        hyp = math.sqrt(dx**2+dz**2)
        
        # normalisation du vecteur + application speed
        dx = (dx/hyp)*speed
        dz = (dz/hyp)*speed
        
        # application du vecteur deplacement
        self.transformation.translation.x += dx
        self.transformation.translation.z += dz
    
    def get_direction(self):
        
        # retourne le vecteur direction en 2D (X,Z) en fonction de l'orientation de l'objet
        
        # récupération de l'angle
        angle = self.transformation.rotation_euler[pyrr.euler.index.yaw]
        
        # ancre
        ancre = -math.pi/2
        corrected_angle = angle - ancre

        # calcul des composantes du vecteur direction
        dx = math.cos(corrected_angle)
        dz = math.sin(corrected_angle)

        return dx, dz

class Camera:
    def __init__(self, transformation = Transformation3D(translation=pyrr.Vector3([0, 1, 0], dtype='float32')), projection = pyrr.matrix44.create_perspective_projection(60, 1, 0.01, 5000)):
        self.transformation = transformation
        self.projection = projection

class Text(Object):
    def __init__(self, value, bottomLeft, topRight, vao, nb_triangle, program, texture):
        self.value = value
        self.bottomLeft = bottomLeft
        self.topRight = topRight
        super().__init__(vao, nb_triangle, program, texture)

    def draw(self):
        GL.glUseProgram(self.program)
        GL.glDisable(GL.GL_DEPTH_TEST)
        size = self.topRight-self.bottomLeft
        size[0] /= len(self.value)
        loc = GL.glGetUniformLocation(self.program, "size")
        if (loc == -1) :
            print("Pas de variable uniforme : size")
        GL.glUniform2f(loc, size[0], size[1])
        GL.glBindVertexArray(self.vao)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        for idx, c in enumerate(self.value):
            loc = GL.glGetUniformLocation(self.program, "start")
            if (loc == -1) :
                print("Pas de variable uniforme : start")
            GL.glUniform2f(loc, self.bottomLeft[0]+idx*size[0], self.bottomLeft[1])

            loc = GL.glGetUniformLocation(self.program, "c")
            if (loc == -1) :
                print("Pas de variable uniforme : c")
            GL.glUniform1i(loc, np.array(ord(c), np.int32))

            GL.glDrawElements(GL.GL_TRIANGLES, 3*2, GL.GL_UNSIGNED_INT, None)
        GL.glEnable(GL.GL_DEPTH_TEST)

    @staticmethod
    def initalize_geometry():
        p0, p1, p2, p3 = [0, 0, 0], [0, 1, 0], [1, 1, 0], [1, 0, 0]
        geometrie = np.array([p0+p1+p2+p3], np.float32)
        index = np.array([[0, 1, 2]+[0, 2, 3]], np.uint32)
        vao = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(vao)
        vbo = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, geometrie, GL.GL_STATIC_DRAW)
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        vboi = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER,vboi)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER,index,GL.GL_STATIC_DRAW)
        return vao

