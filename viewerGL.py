#!/usr/bin/env python3

import OpenGL.GL as GL
import glutils
import glfw
import pyrr
import numpy as np
from cpe3d import Object3D, Text , Transformation3D
import time
from world import World,get_spaceship_parameters
import mesh


INVINCIBLE = True

class ViewerGL:
    
    # attributs utiles pour l'incrémentations des mouvements de la caméra
    increment_go = 0.008
    increment_return = 0.01
    increment_limit_R_L = 0.05
    increment_limit_up_down = 0.3
    i_left, i_right, i_up, i_down = 0,0,0,0

    
    # INITIALISATION
    
    def __init__(self,fullscreen=False):
        
        print(" -- INITIALISAION DE LA FENETRE -- ")
        
        # initialisation de la librairie GLFW
        glfw.init()
        
        # paramétrage du context OpenGL
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        
        # création et paramétrage de la fenêtre
        glfw.window_hint(glfw.RESIZABLE, False)
        
        ## get the monitor for the fullscreen mode
        monitor = glfw.get_primary_monitor()
        mode = glfw.get_video_mode(monitor)
        self.width, self.height = 800,800
        
        if fullscreen:
            self.width, self.height = mode.size.width, mode.size.height

        self.window = glfw.create_window(self.width, self.height, 'OpenGL', None, None)
        
        if fullscreen:
            glfw.set_window_monitor(self.window, monitor, 0, 0, self.width, self.height, glfw.DONT_CARE)

        # paramétrage de la fonction de gestion des évènements
        glfw.set_key_callback(self.window, self.key_callback)
        # activation du context OpenGL pour la fenêtre
        glfw.make_context_current(self.window)
        glfw.swap_interval(1)
        # activation de la gestion de la profondeur
        GL.glEnable(GL.GL_DEPTH_TEST)
        # choix de la couleur de fond
        # GL.glClearColor(0.12, 0.15, 0.17, 1.0)
        GL.glClearColor(0.05, 0.05, 0.05, 1.0)
        print(f"OpenGL: {GL.glGetString(GL.GL_VERSION).decode('ascii')}")



        ## Vecteur de resize des elements
        self.resize = [2, 2*self.width/self.height, 2, 1]
        
        ## distance de la camera
        self.cam_distance = 7 + 3*self.width/self.height
        
        
        
        ## labels
        self.fps = []
        
        
        # mode de boucle de jeu : menu ou game
        self.mode = 'menu'
        
        # temps de début de la boucle de jeu
        self.begin_time = 0
        self.score = 0
        
        ## GAME

        self.objs = {} # dic of objects, draw in the matrix
        self.objs['spaceships'] = []
        self.objs['meteorites'] = []
        self.objs['planets'] = []
        self.objs['portal'] = []
        
        
        
        self.labels = [] # list of labels, always draw, but on the screen
        self.touch = {}
        
        ## MENU

        self.objs_menu = [] # list of objects, draw in the matrix but only in menu mode
        self.labels_menu = [] # list of labels, always draw, but on the screen but only in menu mode
        self.spaceship_selection_menu = 0 # index of the spaceship selected in the menu
        
        print(" -- FIN INITIALISAION DE LA FENETRE -- ")

    def init_program(self,program3d,programGUI,font_texture):

        ## initialisation des shaders
        self.program3d_id = program3d
        self.programGUI_id = programGUI
        
        ## font texture
        self.font_texture = font_texture
        
        
        ## creation des labels
        self.create_labels()
        
        ## initialisation du menu
        self.init_menu()

    def reset_game(self):
        
        # supprime correctement les objets puis relance le menu
        self.objs = {}
        self.objs['spaceships'] = []
        self.objs['meteorites'] = []
        self.objs['planets'] = []
        self.objs['portal'] = []
        
        # reset la caméra
        self.cam.transformation = Transformation3D()
        
        # temps de début de la boucle de jeu
        self.begin_time = 0
        self.score = 0
        
        # relance le menu
        self.mode = 'menu'
        self.init_menu()
        
    def win_game(self):
        
        
        # calcul du temps de jeu
        self.score = time.time() - self.begin_time
        self.text_score.value = f"score : {self.score:.2f} s"
        
        
        # bascule en mode jeu gagné
        self.mode = 'won'
        
        global INVINCIBLE
        INVINCIBLE = True
        self.world.spaceship.speed = self.world.spaceship.hyperspeed
        
        
    # BOUCLE DE JEU
    
    def run(self):
        
        self.tick = 0
        
        # boucle d'affichage
        while not glfw.window_should_close(self.window):
            
            debut = time.time()
            
            # nettoyage de la fenêtre : fond et profondeur
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
            
            ## tick
            self.tick += 1
            
            ## update joystick events
            self.update_joystick()
            
            if (self.mode == 'menu'):

                # KEYBOARD
                self.update_key_menu()
                
                # UPDATE LABELS
                self.update_labels_menu()
                
                # DRAW
                self.update_camera(self.objs_menu[0].program)
                for obj in self.objs_menu:
                    GL.glUseProgram(obj.program)
                    obj.draw()
                    
                for label in self.labels_menu:
                    label.draw()
                
            elif (self.mode == 'game'):
                
                ## WORLD
                self.world.update()
                

                # KEYBOARD
                self.update_key()


                # GESTION COLLISIONS
                self.world.update_collisions()               
                
                
                
                    
                # UPDATE LABELS
                if self.UI_VISIBLE:
                    self.update_labels()
            

                # DRAW
                self.update_camera(self.objs['spaceships'][0].program)
                for type_obj in self.objs:
                    for obj in self.objs[type_obj]:
                        GL.glUseProgram(obj.program)
                        obj.draw()
                        
                for spaceship in [self.world.spaceship]:
                    for ray in spaceship.rayons:
                        GL.glUseProgram(ray.obj.program)
                        ray.obj.draw()
                    
                if self.UI_VISIBLE:
                    for label in self.labels:
                        label.draw()
            
            
                # on verifie si le vaisseau est mort
                if (self.world.spaceship.life <= 0 and not INVINCIBLE):
                    
                    # calcul du temps de jeu
                    self.text_spd.value = "vitesse max : "+self.label_speed.value
                    
                    # bascule en mode gameover
                    self.mode = "gameover"
            
            elif (self.mode == 'won'):
                
                ## WORLD
                self.world.update()

                # GESTION COLLISIONS
                self.world.update_collisions()  


                # KEYBOARD
                self.update_key()

                # DRAW
                self.update_camera(self.objs['spaceships'][0].program)
                for type_obj in self.objs:
                    for obj in self.objs[type_obj]:
                        GL.glUseProgram(obj.program)
                        obj.draw()
                        
                # affiche les labels de fin de jeu
                self.text_congrats.draw()
                self.text_thanks.draw()
                self.text_score.draw()
            
            elif self.mode == "gameover":
            

                # DRAW
                self.update_camera(self.objs['spaceships'][0].program)
                for type_obj in self.objs:
                    for obj in self.objs[type_obj]:
                        GL.glUseProgram(obj.program)
                        obj.draw()
                
                # affiche les labels de fin de jeu
                self.text_gameover.draw()
                self.text_spd.draw()
            
            
            # changement de buffer d'affichage pour éviter un effet de scintillement
            glfw.swap_buffers(self.window)
            # gestion des évènements
            glfw.poll_events()
            
            # maj fps
            self.fps.append(time.time() - debut)
            if len(self.fps) > 100:
                self.fps.pop(0)
            moy = sum(self.fps)/len(self.fps)
            self.label_fps.value = f"{1/moy:.0f} FPS"


    # AJOUT D'OBJETS
 
    def add_object(self, obj, label='meteorites'):
        self.objs[label].append(obj)

    def add_label(self, label):
        self.labels.append(label)

    def add_object_menu(self, obj):
        self.objs_menu.append(obj)

    def add_label_menu(self, label):
        self.labels_menu.append(label)


    # GESTION DES LABELS

    def create_labels(self):
        
        self.UI_VISIBLE = True
        vao = Text.initalize_geometry()
        
        # MENU
        
        title = Text('Space Travel', np.array([-0.7,0.5], np.float32), np.array([0.7, 0.9], np.float32), vao, 2, self.programGUI_id, self.font_texture)
        self.add_label_menu(title)
        
        rules1 = Text('vous devez trouver le portail de', np.array([-0.4,0.4], np.float32), np.array([0.4, 0.45], np.float32), vao, 2, self.programGUI_id, self.font_texture)
        self.add_label_menu(rules1)
        
        rules2 = Text('propulsion dans l\'hyper espace !', np.array([-0.4,0.35], np.float32), np.array([0.4, 0.4], np.float32), vao, 2, self.programGUI_id, self.font_texture)
        self.add_label_menu(rules2)
        
        rules3 = Text('attention aux meteorites ...', np.array([-0.4,0.3], np.float32), np.array([0.4, 0.35], np.float32), vao, 2, self.programGUI_id, self.font_texture)
        self.add_label_menu(rules3)
        
        enter = Text('choisissez votre vaisseau et appuyez sur ESPACE', np.array([-0.7,-0.9], np.float32), np.array([0.7, -0.83], np.float32), vao, 2, self.programGUI_id, self.font_texture)
        self.add_label_menu(enter)
        
        
        # space ship parameters
        self.label_menu_name = Text('...', np.array([-0.3,-0.7], np.float32), np.array([0.3, -0.6], np.float32), vao, 2, self.programGUI_id, self.font_texture)
        self.add_label_menu(self.label_menu_name)
        self.label_menu_life = Text('vie : x', np.array([-0.8,-0.1], np.float32), np.array([-0.6, -0.05], np.float32), vao, 2, self.programGUI_id, self.font_texture)
        self.add_label_menu(self.label_menu_life)
        self.label_menu_maniab = Text('maniabilite : x', np.array([0.4,-0.1], np.float32), np.array([0.8, -0.05], np.float32), vao, 2, self.programGUI_id, self.font_texture)
        self.add_label_menu(self.label_menu_maniab)
        
        
        
        
        
        # GAME OVER        
        self.text_gameover = Text('GAME OVER', np.array([-0.7,-0.1], np.float32), np.array([0.7, 0.1], np.float32), vao, 2, self.programGUI_id, self.font_texture)
        self.text_spd = Text('vitesse : 0', np.array([-0.6,-0.8], np.float32), np.array([0.6, -0.7], np.float32), vao, 2, self.programGUI_id, self.font_texture)
        
        # GAME WON
        self.text_congrats = Text('CONGRATULATIONS !', np.array([-0.7,0.2], np.float32), np.array([0.7, 0.5], np.float32), vao, 2, self.programGUI_id, self.font_texture)
        self.text_thanks = Text('the galaxy is safer with you !', np.array([-0.5,0.1], np.float32), np.array([0.5, 0.15], np.float32), vao, 2, self.programGUI_id, self.font_texture)
        self.text_score = Text('score : 0', np.array([-0.2,-0.8], np.float32), np.array([0.2, -0.7], np.float32), vao, 2, self.programGUI_id, self.font_texture)

        
        # fps
        self.label_fps = Text('FPS : 0', np.array([-0.8,0.7], np.float32), np.array([-0.5, 0.8], np.float32), vao, 2, self.programGUI_id, self.font_texture)
        self.add_label(self.label_fps)
        
        # life
        self.label_life = Text('O O X', np.array([-0.2,0.9], np.float32), np.array([0.2, 0.95], np.float32), vao, 2, self.programGUI_id, self.font_texture)
        self.add_label(self.label_life)
        
        # speed
        self.label_speed = Text('... km/h', np.array([0.45,0.25], np.float32), np.array([0.8, 0.3], np.float32), vao, 2, self.programGUI_id, self.font_texture)
        self.add_label(self.label_speed)
        
        # distance portal
        self.label_portal = Text('... km', np.array([-0.35,-0.95], np.float32), np.array([0.35, -0.9], np.float32), vao, 2, self.programGUI_id, self.font_texture)
        self.add_label(self.label_portal)
        
    def update_labels(self):

        # life
        if INVINCIBLE:
            self.label_life.value = "  invincible  "
        else:
            vie = self.world.spaceship.life
            max_vie = self.world.spaceship.max_life
            self.label_life.value = "O "*vie + "X "*(max_vie-vie)
        
        # speed
        spaceship = self.world.spaceship
        spd = spaceship.speed
        rand_nb = np.random.randint(100, 1000)
        self.label_speed.value = f"{spd:.3f}."+str(rand_nb)+" km/h"
        
        # distance portal
        x1,y1,z1 = self.world.portal.obj.transformation.translation
        x2,y2,z2 = spaceship.obj.transformation.translation
        
        dist = np.sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)*100
        self.label_portal.value = "distance du portail : "+self.str_number(dist)+" km"
        
        

    # GESTION DES TOUCHES
            
    def key_callback(self, win, key, scancode, action, mods):
        
        
        self.touch[key] = action
        
        ## GESTION DES TOUCHES POUR LE MENU
        
        if (self.mode == 'menu'):
            
            # sortie du programme si appui sur la touche 'échappement'
            if key in [glfw.KEY_ESCAPE,'B'] and action == glfw.PRESS:
                glfw.set_window_should_close(win, glfw.TRUE)
            
            # on change de vaisseau si on appuie sur 'flèche gauche' ou 'flèche droite'
            elif key in [glfw.KEY_LEFT,glfw.KEY_A,'left'] and action == glfw.PRESS:
                self.switch_vaisseau_menu('L')
            elif key in [glfw.KEY_RIGHT,glfw.KEY_D,'right'] and action == glfw.PRESS:
                self.switch_vaisseau_menu('R')
        else :
            
            # on revient au menu si on appuie sur 'échap'
            if key in [glfw.KEY_ESCAPE,'B'] and action == glfw.PRESS:
                self.reset_game()
                
        ## RETOUR AU MENU APRES GAME OVER / VICTOIRE
        
        if (self.mode == 'gameover' or self.mode == 'won'):
            if key in [glfw.KEY_ENTER,glfw.KEY_SPACE,'A'] and action == glfw.PRESS:
                self.reset_game()
        
        ## GESTION DES TOUCHES EN SINGLE POUR LE JEU
        
        if (self.mode == 'game'):
            if key in [glfw.KEY_SPACE,'R1','L1'] and action == glfw.PRESS:
                self.world.spaceship.shoot()
                
            if key in [glfw.KEY_F1] and action == glfw.PRESS:
                
                # toggle visibility of the UI
                self.UI_VISIBLE = not self.UI_VISIBLE
        

    def update_key(self):
        
        
        # ----------ROTATION DE LA CAM --------------

        #La camera suit toujours le vaisseau
        self.cam.transformation.rotation_euler = self.objs['spaceships'][0].transformation.rotation_euler.copy() 
        self.cam.transformation.rotation_euler[pyrr.euler.index().yaw] += np.pi

        
        
        # ----------DEPLACEMENT DU VAISSEAU --------------
        
        # Avance tout droit toujours dans la direction de la camera
        self.objs['spaceships'][0].transformation.translation += pyrr.matrix33.apply_to_vector(pyrr.matrix33.create_from_eulers(self.objs['spaceships'][0].transformation.rotation_euler),\
            pyrr.Vector3([0, 0, self.world.spaceship.speed]))
        
        
        
        # ----------DEPLACEMENT VIA CONTROLES --------------
        
        if self.mode == 'game':
            
            maniab = self.world.spaceship.maniab
            
            # on monte avec Z, Fleche haut ou joystick haut !
            if (glfw.KEY_UP in self.touch and self.touch[glfw.KEY_UP] > 0) or (glfw.KEY_W in self.touch and self.touch[glfw.KEY_W] > 0) or self.check_joystick('up'):
                if self.i_up < self.increment_limit_up_down:
                    self.i_up+=self.increment_go
                self.objs['spaceships'][0].transformation.translation -= \
                    pyrr.matrix33.apply_to_vector(pyrr.matrix33.create_from_eulers(self.objs['spaceships'][0].transformation.rotation_euler), pyrr.Vector3([0, -0.2*maniab, 0])) #-0.3
                self.cam.transformation.rotation_euler[pyrr.euler.index().roll] -= self.i_up
            elif self.i_up > 0:
                self.cam.transformation.rotation_euler[pyrr.euler.index().roll] -= self.i_up
                self.i_up-=self.increment_return
                
                
            
            # on descend avec S, flch bas, joy bas
            if (glfw.KEY_DOWN in self.touch and self.touch[glfw.KEY_DOWN] > 0) or (glfw.KEY_S in self.touch and self.touch[glfw.KEY_S] > 0) or self.check_joystick('down'):            
                if self.i_down < self.increment_limit_up_down:
                    self.i_down+=self.increment_go
                self.objs['spaceships'][0].transformation.translation -= \
                    pyrr.matrix33.apply_to_vector(pyrr.matrix33.create_from_eulers(self.objs['spaceships'][0].transformation.rotation_euler), pyrr.Vector3([0, 0.2*maniab, 0]))
                self.cam.transformation.rotation_euler[pyrr.euler.index().roll] += self.i_down
            elif self.i_down > 0:
                self.cam.transformation.rotation_euler[pyrr.euler.index().roll] += self.i_down
                self.i_down-=self.increment_return
            
            
            
            
            # on tourne a gauche avec Q, flch gauche, joy gauche
            if (glfw.KEY_LEFT in self.touch and self.touch[glfw.KEY_LEFT] > 0) or (glfw.KEY_A in self.touch and self.touch[glfw.KEY_A] > 0) or self.check_joystick('left'):
                if self.i_left < self.increment_limit_R_L:
                    self.i_left+=self.increment_go
                self.objs['spaceships'][0].transformation.rotation_euler[pyrr.euler.index().yaw] -= (self.i_left/5)*maniab
                self.cam.transformation.rotation_euler[pyrr.euler.index().yaw] += self.i_left
                
                # on penche légèrement le vaisseau quand on tourne
                # todo : galère parce qu'on ne peut pas utiliser la rotation euler pour ça
                # print(self.objs['spaceships'][0].transformation.rotation_center)
                
            elif self.i_left > 0:
                self.objs['spaceships'][0].transformation.rotation_euler[pyrr.euler.index().yaw] -= (self.i_left/5)*maniab
                self.cam.transformation.rotation_euler[pyrr.euler.index().yaw] += self.i_left
                self.i_left-=self.increment_return
                
                
                
                
            # on tourne a droite avec D, flch droite, joy droite
            if (glfw.KEY_RIGHT in self.touch and self.touch[glfw.KEY_RIGHT] > 0) or (glfw.KEY_D in self.touch and self.touch[glfw.KEY_D] > 0) or self.check_joystick('right'):
                if self.i_right < self.increment_limit_R_L:
                    self.i_right+=self.increment_go
                self.objs['spaceships'][0].transformation.rotation_euler[pyrr.euler.index().yaw] += (self.i_right/5)*maniab
                self.cam.transformation.rotation_euler[pyrr.euler.index().yaw] -= self.i_right
            elif self.i_right > 0:
                self.objs['spaceships'][0].transformation.rotation_euler[pyrr.euler.index().yaw] += (self.i_right/5)*maniab
                self.cam.transformation.rotation_euler[pyrr.euler.index().yaw] -= self.i_right
                self.i_right -=self.increment_return


        # ----------DEPLACEMENT DE LA CAM --------------

        #La camera suit toujours le vaisseau
        self.cam.transformation.rotation_center = self.objs['spaceships'][0].transformation.translation + self.objs['spaceships'][0].transformation.rotation_center
        self.cam.transformation.translation = self.objs['spaceships'][0].transformation.translation + pyrr.Vector3([np.sin(self.tick/100)/2, 2+np.cos(self.tick/100)/2, self.cam_distance])

        if self.mode == 'game':

            if (glfw.KEY_C in self.touch and self.touch[glfw.KEY_C] > 0) \
                or self.check_joystick('Y'):
                
                # on regarde derrère le vaisseau
                self.cam.transformation.rotation_euler[pyrr.euler.index().yaw] -= np.pi
            
    def update_joystick(self):
        
        # sert à appeler key_callback quand on appuie sur un bouton du joystick
        
        for key in ["up","down","left","right","A","B","X","Y","R1","L1"]:
            if self.check_joystick(key):
                if self.touch[key] == 0:
                    self.key_callback(self.window, key,None, glfw.PRESS, None)
            else:
                self.touch[key] = 0
        
    def check_joystick(self, bouton):
        
        # si il n'y a pas de joystick, on ne fait rien        
        if not glfw.joystick_present(0):
            return False
               
        
        # on récupère les axes du joystick
        axes,nb_axes = glfw.get_joystick_axes(0)
        
        # print('axes :',axes,'nb_axes :',nb_axes)
        
        # print(axes[0],axes[1],axes[2],axes[3],axes[4],axes[5])
        
        
        # pour chaque bouton, on vérifie si l'axe correspondant est assez enfoncé
        if bouton == "up":
            if axes[1] < -0.5:
                return True
        elif bouton == "down":
            if axes[1] > 0.5:
                return True
        elif bouton == "left":
            if axes[0] < -0.5:
                return True
        elif bouton == "right":
            if axes[0] > 0.5:
                return True
        elif bouton == "R1":
            if axes[5] > 0.5:
                return True
        elif bouton == "L1":
            if axes[4] > 0.5:
                return True
            
        # on check les boutons
        btns,nb_btns = glfw.get_joystick_buttons(0)
        
        # print('btns :',btns,'nb_btns :',nb_btns)
        
        # print('A :',btns[0],'B :',btns[1],'X :',btns[2],'Y :',btns[3],'R2 :',btns[4],'L2 :',btns[5])
        # print('start :',btns[6],'sel :',btns[7],'L3 :',btns[8],'R3 :',btns[9],'-> :',btns[10],'^ :',btns[11])
        # print('<- :',btns[12],'v :',btns[13],'R2 :',btns[14],'L2 :',btns[15],'L1 :',btns[16],'R1 :',btns[17])
        
        if bouton == "A":
            if btns[0] == 1:
                return True
        elif bouton == "B":
            if btns[1] == 1:
                return True
        elif bouton == "X":
            if btns[2] == 1:
                return True
        elif bouton == "Y":
            if btns[3] == 1:
                return True
            
        
        return False
        

    # GESTION DE LA CAMERA

    def set_camera(self, cam):
        self.cam = cam

    def update_camera(self, prog):
        GL.glUseProgram(prog)
        # Récupère l'identifiant de la variable pour le programme courant
        loc = GL.glGetUniformLocation(prog, "translation_view")
        # Vérifie que la variable existe
        if (loc == -1) :
            print("Pas de variable uniforme : translation_view")
        # Modifie la variable pour le programme courant
        translation = -self.cam.transformation.translation
        GL.glUniform4f(loc, translation.x, translation.y, translation.z, 0)

        # Récupère l'identifiant de la variable pour le programme courant
        loc = GL.glGetUniformLocation(prog, "rotation_center_view")
        # Vérifie que la variable existe
        if (loc == -1) :
            print("Pas de variable uniforme : rotation_center_view")
        # Modifie la variable pour le programme courant
        rotation_center = self.cam.transformation.rotation_center
        GL.glUniform4f(loc, rotation_center.x, rotation_center.y, rotation_center.z, 0)

        rot = pyrr.matrix44.create_from_eulers(-self.cam.transformation.rotation_euler)
        loc = GL.glGetUniformLocation(prog, "rotation_view")
        if (loc == -1) :
            print("Pas de variable uniforme : rotation_view")
        GL.glUniformMatrix4fv(loc, 1, GL.GL_FALSE, rot)
    
        loc = GL.glGetUniformLocation(prog, "projection")
        if (loc == -1) :
            print("Pas de variable uniforme : projection")
        GL.glUniformMatrix4fv(loc, 1, GL.GL_FALSE, self.cam.projection)
    

    
    # MENU
    
    def init_menu(self):
        
        print(" -- INITIALISAION DU MENU -- ")
        
        # on vide les listes
        self.objs_menu = []
        self.spaceship_selection_menu = 0
        
        # on récupère les chemins des fichiers obj des vaisseaux via json
        # todo : pas de json pour l'instant
        
        vaisseaux = ['ressources/spaceship_1.obj','ressources/spaceship_2.obj','ressources/spaceship_3.obj','ressources/spaceship_4.obj']
    
    
        # on crée les objets correspondants
        
        texture = glutils.load_texture('ressources/texture.jpg')
        
        for i in range(len(vaisseaux)):
            
            # initialise the model
            model = mesh.Mesh.load_obj(vaisseaux[i])

            model.normalize()
            model.apply_matrix(pyrr.matrix44.create_from_scale(self.resize))
            
            # send the model to the GPU            
            vao = model.load_to_gpu()
            nb_triangle = model.get_nb_triangles()

            # apply the position to the transformation
            tr = Transformation3D()
            tr.translation.x = 7*i
            
            # create the object
            o = Object3D(vao, nb_triangle, self.program3d_id, texture, tr)
            self.add_object_menu(o)
        
        
        # on crée un portail au fond
        portal = mesh.Mesh.load_obj('ressources/portal.obj')

        portal.normalize()
        portal.apply_matrix(pyrr.matrix44.create_from_scale(self.resize)*90)
        
        # send the portal to the GPU            
        vao = portal.load_to_gpu()
        nb_triangle = portal.get_nb_triangles()

        # apply the position to the transformation
        tr = Transformation3D()
        tr.translation.z = -100
        tr.translation.x = len(vaisseaux)*7/len(vaisseaux)
        
        # create the object
        o = Object3D(vao, nb_triangle, self.program3d_id, texture, tr)
        self.add_object_menu(o)
        
        
        
        
        # change la couleur de fond
        GL.glClearColor(0.15, 0.15, 0.15, 1.0)
        
        print(" -- FIN INITIALISAION DU MENU -- ")
        
    def update_key_menu(self):
        
        
        
        # ----------ROTATION DU VAISSEAU --------------
        
        self.objs_menu[self.spaceship_selection_menu].transformation.rotation_euler[pyrr.euler.index().yaw] += 0.01
        
        # ----------SUIVI DE LA CAMERA --------------
        
        # dans les x : on se déplace fluidement vers le vaisseau sélectionné
        x_cam = self.cam.transformation.translation.x
        x_vaisseau = self.objs_menu[self.spaceship_selection_menu].transformation.translation.x
        distance_cam_vaisseau_x = np.sqrt(x_cam**2 + x_vaisseau**2)
        
        if distance_cam_vaisseau_x > 0.1:
            dx = 0.5*(x_vaisseau - x_cam)
            self.cam.transformation.translation.x += dx
        else:
            self.cam.transformation.translation.x = x_vaisseau
            
        # dans les y,z : on positionne la caméra précisément
        self.cam.transformation.translation.y = self.objs_menu[self.spaceship_selection_menu].transformation.translation.y + 3
        self.cam.transformation.translation.z = self.objs_menu[self.spaceship_selection_menu].transformation.translation.z + self.cam_distance



        
        # ----------GESTION TOUCHE ENTER GAME--------------

        if (glfw.KEY_ENTER in self.touch and self.touch[glfw.KEY_ENTER] > 0) \
                or (glfw.KEY_SPACE in self.touch and self.touch[glfw.KEY_SPACE] > 0) \
                or self.check_joystick('A'):
                                
            # on crée le monde avec le vaisseau selectionné
            print(" -- INITIALISAION DU MONDE -- ")
            self.world = World(self,self.program3d_id,'spaceship_'+str(self.spaceship_selection_menu+1))
            

            # change la couleur de fond
            GL.glClearColor(0.05, 0.05, 0.05, 1.0)
            
            print(" -- FIN INITIALISAION DU MONDE -- ")
            
            # on passe en mode jeu
            self.mode = "game"
            self.begin_time = time.time()
    
    def update_labels_menu(self):
        
        # met à jour les labels de vie et de maniabilite du vaisseau
        
        model = 'spaceship_'+str(self.spaceship_selection_menu+1)
        data = get_spaceship_parameters(model)
        
        self.label_menu_life.value = "vie : " + str(data['life'])
        self.label_menu_maniab.value = "maniabilite : " + str(data['maniabilite'])
        self.label_menu_name.value = str(data['name'])
        
      
    def switch_vaisseau_menu(self,sens_rotation='L'):
        
        if sens_rotation == 'L':
            
            # on se deplace vers la gauche et on affiche le vaisseau correspondant
            self.spaceship_selection_menu -= 1
            if self.spaceship_selection_menu < 0:
                self.spaceship_selection_menu = len(self.objs_menu)-2
        
        elif sens_rotation == 'R':
            
            # on se deplace vers la droite et on affiche le vaisseau correspondant
            self.spaceship_selection_menu += 1
            if self.spaceship_selection_menu >= len(self.objs_menu)-1:
                self.spaceship_selection_menu = 0
            
        

    # FONCTIONS UTILES
    
    def str_number(self,number):
        # Convertir le nombre en chaîne de caractères
        number_str = str(int(number))
        
        # Créer une liste pour stocker les parties du nombre formatées
        formatted_parts = []
        
        # Parcourir les caractères du nombre en partant de la fin
        for i in range(len(number_str)-1, -1, -1):
            # Ajouter chaque caractère au début de la partie formatée
            formatted_parts.insert(0, number_str[i])
            
            # Ajouter un espace tous les 3 caractères
            if (len(number_str)-i) % 3 == 0:
                formatted_parts.insert(0, ' ')
        
        # Joindre les parties formatées pour former la chaîne finale
        formatted_number = ''.join(formatted_parts)
        
        return formatted_number
