
import os
import OpenGL.GL as GL
import numpy as np
from cpe3d import Object3D, Camera, Transformation3D, Text
from ctypes import sizeof, c_float, c_void_p
import glutils
import pyrr
import mesh
import json

# vitesse initiale du vaisseau
SPEED = 1

# nombre de planetes et de meteorites
NB_PLANET = 50
NB_METEOR = 200

# pourcentage de chance qu'un meteor soit un heal
HEAL_RATIO = 0.1

# distance max entre le joueur et un meteor
REMOVE_METEORITE_DISTANCE = 200

class World():
    
    def __init__(self, viewer,prog,spaceship_model):
        
        # initialise the world
        
        self.width = 30
        self.height = 30
        self.viewer = viewer
        self.prog = prog
        
        # generate objects in the world
        
        self.generate_spaceship(spaceship_model)
        
        self.generate_meteorites()
        
        self.generate_planets()
        
        self.portal = Portal(self.viewer,self.prog)

    ## generate objects
    
    def generate_spaceship(self,model):
        
        self.spaceship = SpaceShip(self.viewer, self.prog,model)    
    
    def generate_meteorites(self):
        
        self.nb_meteor = NB_METEOR
        
        # initialise the model
        
        self.modelMeteor = mesh.Mesh.load_obj('ressources/meteor_1.obj')

        self.modelMeteor.normalize()
        self.modelMeteor.apply_matrix(pyrr.matrix44.create_from_scale(self.viewer.resize))
        self.textureMeteor = glutils.load_texture('ressources/grey.jpg')
        self.textureHealMeteor = glutils.load_texture('ressources/heal.jpg')

        # generate meteorites
        
        self.create_meteorites(self.nb_meteor)
        
        
    def create_meteorites(self, nb):
        
        vao = self.modelMeteor.load_to_gpu()
        nb_triangle = self.modelMeteor.get_nb_triangles()

        for i in range (nb):
            
            # choose a random position            
            tr = self.get_rand_tr_around_player()
            
            # choose a random texture
            texture = self.textureMeteor
            
            # frequence apparition heal
            if np.random.randint(0,1000) < (1-HEAL_RATIO)*10:
                texture = self.textureHealMeteor
            
            # create the object
            o = Object3D(vao, nb_triangle, self.prog, texture, tr, True)
            self.viewer.add_object(o)
    
    def generate_planets(self):
        
        
        # initialise the model
        model = mesh.Mesh.load_obj('ressources/planet.obj')
        model.normalize()
            
        # get textures
        textures = []
        for texture in ['blue.jpg','red.jpg','brown.jpg','bzar.jpg','crystal.jpg','glace.jpg','star.jpg']:
            textures.append(glutils.load_texture('ressources/planets/'+texture))
        
        # generate planets
        self.planets = []
        for i in range(NB_PLANET):
            planet = Planet(self.viewer, self.prog, model, textures)
            self.planets.append(planet)
            
            
            
        # print('generated',NB_PLANET,'planets')


    ## update
    
    def update(self):
        
        # update the spaceship
        self.spaceship.update()
        
        # update the meteorites
        if len(self.viewer.objs['meteorites']) < self.nb_meteor:
            self.create_meteorites(self.nb_meteor - len(self.viewer.objs['meteorites']))
            
        # update the portal
        self.portal.update(self.spaceship)
        

    # GESTION DES COLLISIONS
    
    def update_collisions(self):
    
        # check collisions with meteorites
        indexes_to_pop = []
                
        for i in range(0,len(self.viewer.objs['meteorites'])):
            
            # on check si l'objet collisionne avec le vaisseau
            if self.check_cube_collision(self.spaceship.obj, self.viewer.objs['meteorites'][i]):
                
                # si on collisionne, on regarde si c'est un heal ou un damage
                if self.viewer.objs['meteorites'][i].texture == self.textureMeteor:
                    self.spaceship.life -= 1
                elif self.viewer.objs['meteorites'][i].texture == self.textureHealMeteor:
                    self.spaceship.life += 1
                
                # on supprime l'objet
                indexes_to_pop.append(i)
                
            # on check si la meteorite collisionne avec un rayon
            for ray in self.spaceship.rayons:
                if self.check_cube_collision(ray.obj, self.viewer.objs['meteorites'][i]):
                    
                    # on supprime l'objet
                    indexes_to_pop.append(i)
            
            # on check si l'objet est trop loin -> on le supprime pour le regénérer après
            if self.check_distance_is_far(self.spaceship.obj, self.viewer.objs['meteorites'][i]):
                indexes_to_pop.append(i)
        
        # on supprime les meteorites qui sont trop loin ou qui ont collisionné
        if len(indexes_to_pop) > 0:
            # print("popping %d objects" % len(indexes_to_pop))
            for x in range(len(indexes_to_pop)):
                i = indexes_to_pop[x]
                self.viewer.objs['meteorites'].pop(i-x)
    
    
    
        # check collisions with planets
        for i in range(len(self.planets)):
             if (self.planets[i].check_collision(self.spaceship.obj)):
                self.spaceship.life = 0
                print('collision avec planete',i)
    
    def check_cube_collision(self, obj1, obj2):
        
        collision = True
        
        size = 1
        
        # axe x
        if not (obj1.transformation.translation[0] - size < obj2.transformation.translation[0] + size and \
                obj1.transformation.translation[0] + size > obj2.transformation.translation[0] - size):
            collision = False
        
        # axe y
        if not (obj1.transformation.translation[1] - size < obj2.transformation.translation[1] + size and \
                obj1.transformation.translation[1] + size > obj2.transformation.translation[1] - size):
            collision = False
        
        # axe z
        if not (obj1.transformation.translation[2] - size < obj2.transformation.translation[2] + size and \
                obj1.transformation.translation[2] + size > obj2.transformation.translation[2] - size):
            collision = False
        
        return collision
    
    def check_distance_is_far(self, obj1, obj2):
        
        # check if obj1 is very far from obj2 (> 100)
        
        x1, y1, z1 = obj1.transformation.translation
        x2, y2, z2 = obj2.transformation.translation
        
        distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)
        
        if distance > REMOVE_METEORITE_DISTANCE:
            return True
        return False
    
    ## getters and setters
    
    def get_rand_tr_around_player(self):
        
        # genere des meteorites autour du vaisseau
        # la zone d'apparition est proportionnelle à la vitesse du vaisseau et dirigée dans la direction du vaisseau
        # ainsi il est agréable de jouer meme quand les vitesses deviennent élevées
        
        radius = 100*np.sqrt(self.spaceship.speed)
        
        min_radius = radius/8 # on evite de generer des meteorites trop proches du vaisseau -> s'applique seulement sur l'axe z
        
        # random position
        rx = np.random.uniform(-radius/4, radius/4)
        ry = np.random.uniform(-radius/2, radius/2)
        
        # on choisit soit une position devant le vaisseau, soit une position derriere
        rzs = [np.random.uniform(min_radius, radius), np.random.uniform(-radius, -min_radius)]
        rz = rzs[np.random.randint(0,2)]
        
        # apply the direction of the spaceship
        tr = Transformation3D()
        tr.translation += pyrr.matrix33.apply_to_vector(pyrr.matrix33.create_from_eulers(self.viewer.objs['spaceships'][0].transformation.rotation_euler),\
            pyrr.Vector3([rx,ry,rz]))
        tr.translation += self.viewer.objs['spaceships'][0].transformation.translation
        
        # rotation aleatoire
        tr.rotation_euler[pyrr.euler.index().yaw] += np.random.uniform(0, 2*np.pi)
        
        
        return tr

class SpaceShip():
    
    # initialise the spaceship
    
    def __init__(self, viewer, prog,model=None):
        
        ## init
        self.viewer = viewer
        self.prog = prog
        
        if model == None:
            self.fullPathModel = 'ressources/spaceship_1.obj'
            self.model = 'spaceship_1'
        else:
            self.fullPathModel = 'ressources/'+model+'.obj'
            self.model = model
        
        ## creation 3D object
        self.create_3D_Object()
        
        
        ## movement
        self.speed = SPEED
        self.acceleration = 0.000001
        self.accofacc = 0.0000001
        self.hyperspeed = 50
        
        
        ## PARAMETRES QUI CHANGENT SELON LE VAISSEAU CHOISI
        self.apply_spaceship_param()
        
        # rayons lasers
        
        self.rayons = []
        
    def create_3D_Object(self):
        
        # initialise the model
        
        self.modelSpaceship = mesh.Mesh.load_obj(self.fullPathModel)

        self.modelSpaceship.normalize()
        self.modelSpaceship.apply_matrix(pyrr.matrix44.create_from_scale(self.viewer.resize))
        texture = glutils.load_texture('ressources/texture.jpg')

        # send the model to the GPU        
        vao = self.modelSpaceship.load_to_gpu()
        nb_triangle = self.modelSpaceship.get_nb_triangles()

        # apply the position to the transformation
        tr = Transformation3D()
        tr.translation.y = -np.amin(self.modelSpaceship.vertices, axis=0)[1]
        tr.translation.z = -5
        tr.rotation_center.z = 0.2
        
        # create the object
        self.obj = Object3D(vao, nb_triangle, self.prog, texture, tr)
        self.viewer.add_object(self.obj, 'spaceships')
        
        # self.viewer.add_object_menu(o)
        
    def apply_spaceship_param(self):
        
        data = get_spaceship_parameters(self.model)
        
        # applique les paramètres récupérés
        
        ## life
        self.max_life = data['life']
        self.life = self.max_life
        
        ## maniabilité
        self.maniab = data['maniabilite']
        
        
    ## update
    
    def update(self):
            
        # update speed
        self.speed += self.acceleration
        
        # update acceleration
        self.acceleration += self.accofacc
        
        # update the shoots
        for ray in self.rayons:
            
            # on avance le rayon
            ray.update()
            
            # check si le rayon est trop loin
            indexes_to_pop = []
            for i in range(0,len(self.rayons)):
                # on check si l'objet est trop loin -> on le supprime
                if self.check_distance_is_far(self.obj, self.rayons[i].obj):
                    indexes_to_pop.append(i)
            # on supprime les rayons qui sont trop loin
            if len(indexes_to_pop) > 0:
                # print("popping %d objects" % len(indexes_to_pop))
                for x in range(len(indexes_to_pop)):
                    i = indexes_to_pop[x]
                    self.rayons.pop(i-x)
            
        
    def shoot(self):
        
        # on envoie un rayon laser
        # pew pew
        
        # direction
        direction = self.obj.get_direction()
        
        # position
        pos = self.obj.transformation.translation.copy()
        pos.x += np.random.rand() -0.5
        pos.y += np.random.rand() -0.5
        pos.z += np.random.rand() -0.5
        
        
        speed = self.speed + 8
        
        rayon = RayonLaser(self.viewer, self.prog, pos, direction,speed)
        
        self.rayons.append(rayon)

    def check_distance_is_far(self, obj1, obj2):
        
        # check if obj1 is very far from obj2 (> 100)
        
        x1, y1, z1 = obj1.transformation.translation
        x2, y2, z2 = obj2.transformation.translation
        
        distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)
        
        if distance > REMOVE_METEORITE_DISTANCE:
            return True
        return False
    
class RayonLaser():
    
    def __init__(self,viewer,prog,pos,direc,speed):
        
        ## init
        self.viewer = viewer
        self.prog = prog
        
        # on crée le modele
        self.size = 2
        self.create_3D_Object(pos)
        
        # on met à jour sa position
        # self.obj.transformation.translation = tr
        
        # on tourne le modele dans la direction d'avancement
        self.obj.rotate_to_dir(direc)
        self.direc = direc
        
        # speed
        self.speed = speed
        
    def create_3D_Object(self,pos):
        
        # initialise the model
        
        self.modelRayon = mesh.Mesh.load_obj('ressources/rayon_laser.obj')

        self.modelRayon.normalize()
        self.modelRayon.apply_matrix(pyrr.matrix44.create_from_scale(self.viewer.resize)*self.size)
        texture = glutils.load_texture('ressources/white.jpg')

        # send the model to the GPU        
        vao = self.modelRayon.load_to_gpu()
        nb_triangle = self.modelRayon.get_nb_triangles()

        # apply the position to the transformation
        tr = Transformation3D()
        tr.translation = pos
        
        # create the object
        self.obj = Object3D(vao, nb_triangle, self.prog, texture, tr)
        # self.viewer.add_object(self.obj, 'rayons')
        
    def update(self):
        
        # on avance
        self.obj.move_to_dir(self.direc,self.speed)     
             
class Planet():
    
    def __init__(self,viewer,prog,model,textures):
        
        self.viewer = viewer
        self.prog = prog
        
        self.create_3D_Object(model,textures)

    def create_3D_Object(self,model,textures):
        
        self.modelPlanet = model.copy()
        nb_triangle = model.get_nb_triangles()
            
        # choose a random size
        self.size = np.random.uniform(20,200)
        self.modelPlanet.apply_matrix(pyrr.matrix44.create_from_scale(self.viewer.resize)*self.size)
        
        # choose a random texture
        self.texture = textures[np.random.randint(0,len(textures))]
        
        # check vao
        vao = self.modelPlanet.load_to_gpu()
        
        # choose a random position
        tr = self.get_rand_tr_far_away()
        
        # create the object
        self.obj = Object3D(vao, nb_triangle, self.prog, self.texture, tr, True)
        self.viewer.add_object(self.obj, 'planets')

    def get_rand_tr_far_away(self):
        
        radius = 3000
        
        # random position
        rx = np.random.uniform(-radius, radius)
        ry = np.random.uniform(-radius, radius)
        rz = np.random.uniform(-radius, radius)
        
        tr = Transformation3D()
        tr.translation[0] = rx
        tr.translation[1] = ry
        tr.translation[2] = rz
        
        # rotation aleatoire
        tr.rotation_euler[pyrr.euler.index().yaw] += np.random.uniform(0, 2*np.pi)
        
        return tr
        
    def check_collision(self,obj1):
        
        # return True si tr est dans la sphere de la planete
        
        # calcule la distance entre le centre de la planete et le point tr
        x1, y1, z1 = obj1.transformation.translation
        x2, y2, z2 = self.obj.transformation.translation
        
        distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)
        
        rayon = self.size*self.viewer.resize[0]*1.2
        
        if distance <= rayon:
            return True
        return False
    
class Portal():
    
    def __init__(self,viewer,prog):
        
        self.viewer = viewer
        self.prog = prog
        
        self.create_3D_Object()
        
        self.direc = self.obj.get_direction()

    def create_3D_Object(self):
        
        self.modelPortal = mesh.Mesh.load_obj('ressources/portal.obj')

        self.modelPortal.normalize()
        nb_triangle = self.modelPortal.get_nb_triangles()
            
        # choose a random size
        self.size = 10
        self.modelPortal.apply_matrix(pyrr.matrix44.create_from_scale(self.viewer.resize)*self.size)
        
        # choose a random texture
        texture = glutils.load_texture('ressources/texture.jpg')
        
        # check vao
        vao = self.modelPortal.load_to_gpu()
        
        # choose a random position
        tr = self.get_rand_tr_far_away()
        
        # create the object
        self.obj = Object3D(vao, nb_triangle, self.prog, texture, tr)
        self.viewer.add_object(self.obj, 'portal')

    def get_rand_tr_far_away(self):
        
        radius = 2000
        
        # random position
        rx = np.random.uniform(-radius, radius)
        ry = np.random.uniform(-radius, radius)
        rz = np.random.uniform(-radius, radius)
        
        tr = Transformation3D()
        tr.translation[0] = rx
        tr.translation[1] = ry
        tr.translation[2] = rz
        
        # rotation aleatoire
        tr.rotation_euler[pyrr.euler.index().yaw] += np.random.uniform(0, 2*np.pi)
        
        return tr

    def update(self,spaceship):
        
        # calcul de la distance de la spaceship & du portal
        
        x1,y1,z1 = self.obj.transformation.translation
        x2,y2,z2 = spaceship.obj.transformation.translation
        
        dist = np.sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)
        if dist < 60 :
            
            direc_finale = spaceship.obj.get_direction()
            
            # on inverse la direction
            direc_finale = -direc_finale[0],-direc_finale[1]
            
            pourcentage_direc_initiale = (dist-10)/50
            
            if pourcentage_direc_initiale < 0:
                pourcentage_direc_initiale = 0
            
            direc = direc_finale[0]*(1-pourcentage_direc_initiale) + self.direc[0]*pourcentage_direc_initiale, \
                    direc_finale[1]*(1-pourcentage_direc_initiale) + self.direc[1]*pourcentage_direc_initiale
            
            # on tourne le portail
            self.obj.rotate_to_dir(direc)
            
            # check collisions
            if dist <= 10:
                self.viewer.win_game()

def get_spaceship_parameters(model):
        
    # lit le fichier 'spaceships.json' et récupère les bons paramètres du vaisseau
    # en fonction du nom du modèle utilisé
    
    data = {}
    
    with open("ressources/spaceships.json",'r') as f:
        data = json.load(f)
        
    return data[model]

