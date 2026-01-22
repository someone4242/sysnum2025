import tkinter as tk
import math

ECHELLE=2 # à modifier si vous voulez une horloge plus petite ou plus grande

LARGEUR = 400*ECHELLE
HAUTEUR = 450*ECHELLE
CENTRE = LARGEUR//2
RAYON = 160*ECHELLE

root = tk.Tk()
canvas = tk.Canvas(root,width=LARGEUR,height=HAUTEUR,bg="black")
canvas.pack()

canvas.create_oval(CENTRE-RAYON,CENTRE-RAYON,CENTRE+RAYON,CENTRE+RAYON,outline="#888",width=4*ECHELLE)
for h in range(12):
    angle = math.radians(h*30-90)
    x1 = CENTRE+math.cos(angle)*(RAYON-10)
    y1 = CENTRE+math.sin(angle)*(RAYON-10)
    x2 = CENTRE+math.cos(angle)*(RAYON-25)
    y2 = CENTRE+math.sin(angle)*(RAYON-25)
    canvas.create_line(x1,y1,x2,y2,fill="#aaa",width=3*ECHELLE)
aiguille_heures = None
aiguille_minutes = None
aiguille_secondes = None
nombre_ids = []
SEGMENTS = {
    '0': [1,1,1,1,1,1,0],
    '1': [0,1,1,0,0,0,0],
    '2': [1,1,0,1,1,0,1],
    '3': [1,1,1,1,0,0,1],
    '4': [0,1,1,0,0,1,1],
    '5': [1,0,1,1,0,1,1],
    '6': [1,0,1,1,1,1,1],
    '7': [1,1,1,0,0,0,0],
    '8': [1,1,1,1,1,1,1],
    '9': [1,1,1,1,0,1,1],
}

def dessin_aiguille(angle_deg,longueur,largeur,couleur):
    angle = math.radians(angle_deg-90)
    x = CENTRE+math.cos(angle)*longueur
    y = CENTRE+math.sin(angle)*longueur
    return canvas.create_line(CENTRE,CENTRE,x,y,fill=couleur,width=largeur,capstyle=tk.ROUND)

def dessin_nombre(x,y,taille,num,couleur="#00ff00"):
    seg_on = SEGMENTS.get(num,[0]*7)
    ids = []
    coords = [
        (x,y,x+taille,y),
        (x+taille,y,x+taille,y+taille),
        (x+taille,y+taille,x+taille,y+2*taille),
        (x,y+2*taille,x+taille,y+2*taille),
        (x,y+taille,x,y+2*taille),
        (x,y,x,y+taille),
        (x,y+taille,x+taille,y+taille)
    ]
    for i,on in enumerate(seg_on):
        if on:
            x1,y1,x2,y2 = coords[i]
            ids.append(canvas.create_line(x1,y1,x2,y2,fill=couleur,width=taille//5))
    return ids

def dessin_heure(hh,mm,ss):
    global nombre_ids
    for d in nombre_ids:
        canvas.delete(d)
    nombre_ids = []
    taille = RAYON*0.15
    espace_nombre = taille*1.5
    espace_point = taille
    debut_x = CENTRE-(espace_nombre*2+espace_point+espace_nombre*2+espace_point+espace_nombre*2)/2
    debut_y = CENTRE+RAYON+taille
    nombres = f"{hh:02d}{mm:02d}{ss:02d}"
    positions = []
    for i,d in enumerate(nombres):
        x_pos = debut_x+i*espace_nombre
        if i>=2:
            x_pos += espace_point
        if i>=4:
            x_pos += espace_point
        positions.append(x_pos)
    for i,d in enumerate(nombres):
        x = positions[i]
        if i==1 or i==3:
            point_x = x+espace_nombre
            nombre_ids.append(canvas.create_text(point_x,debut_y+taille,text=":",fill="#00ff00",font=("Consolas",int(taille)),anchor="w"))
        nombre_ids.extend(dessin_nombre(x,debut_y,taille,d))

def afficher_heure(hh,mm,ss):
    global aiguille_heures,aiguille_minutes,aiguille_secondes
    for aiguille in (aiguille_heures,aiguille_minutes,aiguille_secondes):
        if aiguille:
            canvas.delete(aiguille)
    h_angle = (hh%12)*30+mm*0.5+ss/120
    min_angle = mm*6+ss*0.1
    sec_angle = ss*6
    aiguille_heures = dessin_aiguille(h_angle,RAYON*0.5,6,"#ffffff")
    aiguille_minutes = dessin_aiguille(min_angle,RAYON*0.75,4,"#cccccc")
    aiguille_secondes = dessin_aiguille(sec_angle,RAYON*0.9,2,"#ff2d2d")
    dessin_heure(hh,mm,ss)

while True:
    root.update()
    try:
        with open("time.txt", "r") as f:
            ligne = f.readline().strip()
            nombres = ''.join(c for c in ligne if c.isdigit()).rjust(6, "0")[:6]
            hh = int(nombres[0:2])
            mm = int(nombres[2:4])
            ss = int(nombres[4:6])
            afficher_heure(hh,mm,ss)
    except Exception as e:
        print("Erreur:", e)
