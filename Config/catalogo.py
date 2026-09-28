"""Mascotas destacadas con página de perfil propia (/cachorro, /michi, /rocky).

Se muestran junto a las mascotas publicadas por los administradores en /adopcion.
"""

MASCOTAS_DESTACADAS = {
    "cachorro": {
        "nombre": "Cachorro",
        "imagen": "images/Cachorro.png",
        "especie": "Perro",
        "autor": "Daniel",
        "resumen": "Cachorra schnauzer juguetona e inteligente que busca una familia con tiempo para jugar y pasear.",
        "datos": [
            ("Raza", "Schnauzer miniatura"),
            ("Edad", "3–6 meses"),
            ("Sexo", "Hembra"),
            ("Tamaño adulto", "Pequeño (7–9 kg aprox.)"),
        ],
        "salud": "Vacunada, desparasitada y en buen estado.",
        "caracter": "Juguetona, activa, inteligente y muy leal.",
        "requisitos": "Espacio seguro dentro de casa, tiempo para juegos y paseos diarios, y compromiso con su "
                      "educación y sus cuidados veterinarios.",
        "ubicacion": "Barranquilla, Atlántico · barrio San José",
        "contacto": "+57 302 216 3398",
    },
    "michi": {
        "nombre": "Michi",
        "imagen": "images/michi.jpg",
        "especie": "Gato",
        "autor": "Ana",
        "resumen": "Gatita cariñosa y sociable. Le encanta jugar y recibir mimos: ideal para una familia que "
                   "busca compañía tierna.",
        "datos": [
            ("Raza", "Criolla"),
            ("Edad", "8 meses"),
            ("Sexo", "Hembra"),
            ("Esterilizada", "Sí"),
        ],
        "salud": "Vacunada, desparasitada y esterilizada.",
        "caracter": "Muy cariñosa, juguetona y sociable con otros gatos.",
        "requisitos": "Hogar responsable, protección en ventanas, compromiso con su bienestar y controles "
                      "veterinarios.",
        "ubicacion": "Barranquilla, Atlántico",
        "contacto": "+57 300 123 4567",
    },
    "rocky": {
        "nombre": "Rocky",
        "imagen": "images/chiki.jpg",
        "especie": "Perro",
        "autor": "Andrea",
        "resumen": "Perrito mestizo de tamaño mini, noble y protector. Disfruta el aire libre y convive bien con "
                   "personas y otros animales.",
        "datos": [
            ("Raza", "Mestizo"),
            ("Edad", "2 años"),
            ("Sexo", "Macho"),
            ("Tamaño", "Miniatura (4 kg aprox.)"),
        ],
        "salud": "Vacunado, desparasitado y en excelente estado.",
        "caracter": "Noble, protector, juguetón y sociable con personas y otros animales.",
        "requisitos": "Espacio para jugar, paseos diarios, compromiso con su bienestar y controles veterinarios.",
        "ubicacion": "Barranquilla, Atlántico",
        "contacto": "+57 301 234 5678",
    },
}
