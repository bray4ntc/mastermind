import pygame
from pygame.locals import *
from z3 import Solver, Int, And, Or, Not, sat
import random

# Inicialización de Pygame
pygame.init()

# Configuración de la pantalla
PANTALLA_BASE_ANCHO = 800
PANTALLA_BASE_ALTO = 600
ventana = pygame.display.set_mode((PANTALLA_BASE_ANCHO, PANTALLA_BASE_ALTO), RESIZABLE)
pygame.display.set_caption("Mastermind")

# Colores
NEGRO = (0, 0, 0)
GRIS_OSCURO = (50, 50, 50)
BLANCO = (255, 255, 255)
ROJO = (255, 0, 0)
AZUL = (0, 0, 255)
VERDE = (0, 255, 0)
AMARILLO = (255, 255, 0)

# Configuración del juego
colores_disponibles = [ROJO, AZUL, VERDE, AMARILLO]
mapa_colores = {color: i for i, color in enumerate(colores_disponibles)}
tamaño_combinación = 4
max_intentos = 10

class EstadoJuego:
    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        colores_temp = colores_disponibles.copy()
        random.shuffle(colores_temp)
        self.combinación_secreta = colores_temp[:tamaño_combinación]
        
        self.intento_actual = []
        self.intentos = []
        self.resultados = []
        self.mensaje = ""
        self.juego_terminado = False

    def verificar_intento(self, intento):
        # Colores correctos en posición correcta
        colores_posicion_correcta = sum(1 for x, y in zip(intento, self.combinación_secreta) if x == y)
        
        # Colores correctos en posición incorrecta
        colores_posicion_incorrecta = sum(min(intento.count(color), self.combinación_secreta.count(color)) 
                                         for color in set(intento)) - colores_posicion_correcta
        
        return colores_posicion_correcta, colores_posicion_incorrecta

class Botón:
    def __init__(self, color, x, y, radio):
        self.color = color
        self.x = x
        self.y = y
        self.radio = radio

    def dibujar(self, superficie):
        pygame.draw.circle(superficie, self.color, (self.x, self.y), self.radio)
        pygame.draw.circle(superficie, BLANCO, (self.x, self.y), self.radio, 2)

    def esta_sobre(self, pos):
        return ((pos[0] - self.x) ** 2 + (pos[1] - self.y) ** 2) <= self.radio ** 2

class InterfazJuego:
    def __init__(self):
        self.fuente_grande = pygame.font.Font(None, 48)
        self.fuente_normal = pygame.font.Font(None, 36)
        self.fuente_pequeña = pygame.font.Font(None, 24)
        self.actualizar_dimensiones(PANTALLA_BASE_ANCHO, PANTALLA_BASE_ALTO)

    def actualizar_dimensiones(self, ancho, alto):
        self.ancho = ancho
        self.alto = alto
        self.margen = min(ancho, alto) // 20
        self.radio_circulo = min(ancho, alto) // 25
        
        espacio_entre_botones = self.ancho // 8
        inicio_x = self.ancho // 2 - (espacio_entre_botones * 1.5)
        self.botones_colores = [
            Botón(color, inicio_x + i * espacio_entre_botones, 
                  self.alto - self.margen - self.radio_circulo, self.radio_circulo)
            for i, color in enumerate(colores_disponibles)
        ]

    def dibujar_tablero(self, superficie, estado):
        superficie.fill(NEGRO)
        
        # Título
        titulo = self.fuente_grande.render("Mastermind", True, BLANCO)
        superficie.blit(titulo, (self.ancho // 2 - titulo.get_width() // 2, self.margen))

        # Instrucciones
        instrucciones = self.fuente_pequeña.render("Selecciona 4 colores diferentes", True, BLANCO)
        superficie.blit(instrucciones, (10, 10))

        # Dibujar intentos previos y sus resultados
        for i, (intento, resultado) in enumerate(zip(estado.intentos, estado.resultados)):
            y = self.margen * 3 + i * (self.radio_circulo * 3)
            
            # Dibujar colores del intento
            for j, color in enumerate(intento):
                x = self.margen + j * (self.radio_circulo * 2.5)
                pygame.draw.circle(superficie, color, (x, y), self.radio_circulo)
                pygame.draw.circle(superficie, BLANCO, (x, y), self.radio_circulo, 2)
            
            # Mostrar resultado
            pos_correcta, pos_incorrecta = resultado
            resultado_texto = self.fuente_normal.render(
                f"Posición correcta: {pos_correcta}", 
                True, BLANCO)
            superficie.blit(resultado_texto, 
                           (self.margen + tamaño_combinación * (self.radio_circulo * 2.5) + 20, y - 10))

        # Dibujar intento actual
        y_intento_actual = self.alto - self.margen * 3 - self.radio_circulo * 2
        for i, color in enumerate(estado.intento_actual):
            x = self.margen + i * (self.radio_circulo * 2.5)
            pygame.draw.circle(superficie, color, (x, y_intento_actual), self.radio_circulo)
            pygame.draw.circle(superficie, BLANCO, (x, y_intento_actual), self.radio_circulo, 2)

        # Dibujar botones de colores disponibles
        for boton in self.botones_colores:
            boton.dibujar(superficie)

        # Mostrar mensaje de estado del juego
        if estado.mensaje:
            msg_surface = self.fuente_normal.render(estado.mensaje, True, BLANCO)
            superficie.blit(msg_surface, (self.ancho // 2 - msg_surface.get_width() // 2, 
                                         self.alto - self.margen * 2))

        # Si el juego ha terminado, mostrar la combinación secreta
        if estado.juego_terminado:
            secreto_texto = self.fuente_normal.render("Combinación secreta:", True, BLANCO)
            superficie.blit(secreto_texto, (self.margen, self.alto - self.margen * 4))
            for i, color in enumerate(estado.combinación_secreta):
                x = self.margen + (i + 5) * (self.radio_circulo * 2.5)
                y = self.alto - self.margen * 4
                pygame.draw.circle(superficie, color, (x, y), self.radio_circulo)
                pygame.draw.circle(superficie, BLANCO, (x, y), self.radio_circulo, 2)

# Inicialización
interfaz = InterfazJuego()
estado_juego = EstadoJuego()

# Bucle principal
ejecutando = True
while ejecutando:
    for evento in pygame.event.get():
        if evento.type == QUIT:
            ejecutando = False
        elif evento.type == VIDEORESIZE:
            ventana = pygame.display.set_mode((evento.w, evento.h), RESIZABLE)
            interfaz.actualizar_dimensiones(evento.w, evento.h)
        elif evento.type == MOUSEBUTTONDOWN:
            if estado_juego.juego_terminado:
                estado_juego.reiniciar()
            else:
                for boton in interfaz.botones_colores:
                    if boton.esta_sobre(evento.pos):
                        if boton.color not in estado_juego.intento_actual and len(estado_juego.intento_actual) < tamaño_combinación:
                            estado_juego.intento_actual.append(boton.color)
                            
                            if len(estado_juego.intento_actual) == tamaño_combinación:
                                pos_correcta, pos_incorrecta = estado_juego.verificar_intento(estado_juego.intento_actual)
                                estado_juego.resultados.append((pos_correcta, pos_incorrecta))
                                
                                if pos_correcta == tamaño_combinación:
                                    estado_juego.mensaje = "¡Ganaste! Haz clic para jugar de nuevo"
                                    estado_juego.juego_terminado = True
                                else:
                                    estado_juego.intentos.append(estado_juego.intento_actual.copy())
                                    if len(estado_juego.intentos) >= max_intentos:
                                        estado_juego.mensaje = "¡Juego terminado! Haz clic para jugar de nuevo"
                                        estado_juego.juego_terminado = True
                                    estado_juego.intento_actual = []

    interfaz.dibujar_tablero(ventana, estado_juego)
    pygame.display.flip()

pygame.quit()