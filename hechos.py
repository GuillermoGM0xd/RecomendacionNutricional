# HECHOS INICIALES
# Rangos de IMC (kg/m²) para cada categoría de peso.
# Clave externa: nombre de la categoría. Clave interna: límites del rango.
# Para clasificar se usa solo el límite inferior ("min"), de modo que un
# IMC como 29.95 no quede fuera de ningún rango.
HECHOS_IMC_RANGOS = {
    "Sobrepeso":       {"min": 25.0, "max": 29.9},
    "Obesidad Tipo 1": {"min": 30.0, "max": 34.9},
    "Obesidad Tipo 2": {"min": 35.0, "max": 39.9},
    "Obesidad Tipo 3": {"min": 40.0, "max": 200.0},
}

# Coeficiente de actividad física (AF) para adultos de 19 años o más.
# Se consulta como HECHOS_AF[genero][nivel_actividad].
HECHOS_AF = {
    "masculino": {
        "sedentario": 1.00,
        "poco_activo": 1.12,
        "activo": 1.29,
        "muy_activo": 1.59,
    },
    "femenino": {
        "sedentario": 1.00,
        "poco_activo": 1.16,
        "activo": 1.27,
        "muy_activo": 1.44,
    },
}

# Valores permitidos para los datos del usuario (edad en años, altura en metros).
RANGOS_ENTRADA = {"edad": (19, 100), "altura": (1.00, 2.50)}
# HECHOS DINÁMICOS (los llena la interfaz con los datos del usuario)
HECHOS_DINAMICOS = {
    "peso": None,             # kilogramos
    "altura": None,           # metros
    "edad": None,             # años cumplidos (19 a 100)
    "genero": None,           # "masculino" o "femenino"
    "nivel_actividad": None,  # sedentario, poco_activo, activo o muy_activo
}

# HECHOS INFERIDOS (los llenan las reglas)
HECHOS_INFERIDOS = {
    "imc": None,             # R1
    "af": None,              # R5
    "categoria_peso": None,  # R4
    "get": None,             # R2 o R3, en kcal/día
}

# REGLAS DE PRODUCCIÓN
# (Cada regla recibe los hechos dinámicos y los inferidos, y
# agrega su conclusión a los hechos inferidos.)
def r1_calcular_imc(dinamicos, inferidos):
    """R1: SI se conoce el peso (p) y la altura (a) ENTONCES IMC = p / a²."""
    p, a = dinamicos["peso"], dinamicos["altura"]
    if p is not None and a is not None:
        inferidos["imc"] = p / (a ** 2)

def r5_asignar_af(dinamicos, inferidos):
    """R5: SI se conoce el género Y el nivel de actividad ENTONCES se asigna
    el coeficiente AF que le corresponde en la tabla de hechos."""
    genero, nivel = dinamicos["genero"], dinamicos["nivel_actividad"]
    if genero in HECHOS_AF and nivel in HECHOS_AF[genero]:
        inferidos["af"] = HECHOS_AF[genero][nivel]

def r4_clasificar_peso(dinamicos, inferidos):
    """R4: SI ya se calculó el IMC ENTONCES se asigna la categoría de peso
    cuyo rango lo contiene."""
    imc = inferidos["imc"]
    if imc is None:
        return
    # Se recorren las categorías de mayor a menor límite inferior; la primera
    # que cumple imc >= min es la categoría del usuario.
    por_min = sorted(HECHOS_IMC_RANGOS.items(),
                     key=lambda par: par[1]["min"], reverse=True)
    inferidos["categoria_peso"] = "Sin sobrepeso ni obesidad"
    for categoria, rango in por_min:
        if imc >= rango["min"]:
            inferidos["categoria_peso"] = categoria
            break

def r2_r3_calcular_get(dinamicos, inferidos):
    """R2 (hombres) y R3 (mujeres): SI la persona tiene 19 años o más y su
    IMC es mayor o igual a 25 ENTONCES se calcula el gasto energético
    total (GET) en kcal/día con la ecuación de su género."""
    imc, af = inferidos["imc"], inferidos["af"]
    edad, peso, altura = dinamicos["edad"], dinamicos["peso"], dinamicos["altura"]
    if imc is None or af is None or edad is None or edad < 19 or imc < 25:
        return
    if dinamicos["genero"] == "masculino":   # R2
        inferidos["get"] = 1086 - (10.1 * edad) + af * ((13.7 * peso) + (416 * altura))
    elif dinamicos["genero"] == "femenino":  # R3
        inferidos["get"] = 448 - (7.95 * edad) + af * ((11.4 * peso) + (619 * altura))

def validar_entrada(dinamicos):
    """Revisa que los datos capturados estén dentro de los rangos permitidos."""
    for campo, (minimo, maximo) in RANGOS_ENTRADA.items():
        valor = dinamicos[campo]
        if valor is None or not (minimo <= valor <= maximo):
            raise ValueError(f"{campo} debe estar entre {minimo} y {maximo}")
    if dinamicos["genero"] not in HECHOS_AF:
        raise ValueError("genero debe ser 'masculino' o 'femenino'")
    if dinamicos["nivel_actividad"] not in HECHOS_AF[dinamicos["genero"]]:
        raise ValueError("nivel_actividad no válido")
    if dinamicos["peso"] is None or dinamicos["peso"] <= 0:
        raise ValueError("peso debe ser mayor que 0")


def aplicar_reglas(dinamicos):
    """Aplica las reglas en el orden en que dependen unas de otras:
    R1 y R5 primero (no dependen de nadie), luego R4, R2 y R3."""
    validar_entrada(dinamicos)
    inferidos = dict(HECHOS_INFERIDOS)  # copia: no se modifica la plantilla
    r1_calcular_imc(dinamicos, inferidos)
    r5_asignar_af(dinamicos, inferidos)
    r4_clasificar_peso(dinamicos, inferidos)
    r2_r3_calcular_get(dinamicos, inferidos)
    return inferidos
