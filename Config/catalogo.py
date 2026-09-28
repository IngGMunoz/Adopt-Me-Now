"""Mascotas destacadas con las que arranca el catálogo.

Se cargan una sola vez en la base (al crearla o al migrarla); después el administrador
las gestiona desde el panel como cualquier otra mascota.
"""

MASCOTAS_INICIALES = [
    {
        "nombre": "Cachorro",
        "imagen": "images/Cachorro.png",
        "autor": "Daniel",
        "especie": "perro",
        "raza": "Schnauzer miniatura",
        "edad": "3–6 meses",
        "sexo": "hembra",
        "tamanio": "pequeño",
        "ubicacion": "Barranquilla, Atlántico",
        "descripcion": "Cachorra schnauzer juguetona e inteligente que busca una familia con tiempo para jugar y pasear.\n\n"
                       "Salud: vacunada, desparasitada y en buen estado.\n\n"
                       "Carácter: juguetona, activa, inteligente y muy leal.\n\n"
                       "Requisitos: espacio seguro dentro de casa, tiempo para juegos y paseos diarios, y compromiso "
                       "con su educación y sus cuidados veterinarios.",
    },
    {
        "nombre": "Michi",
        "imagen": "images/michi.jpg",
        "autor": "Ana",
        "especie": "gato",
        "raza": "Criolla",
        "edad": "8 meses",
        "sexo": "hembra",
        "tamanio": "pequeño",
        "ubicacion": "Barranquilla, Atlántico",
        "descripcion": "Gatita cariñosa y sociable. Le encanta jugar y recibir mimos: ideal para una familia que busca "
                       "compañía tierna.\n\n"
                       "Salud: vacunada, desparasitada y esterilizada.\n\n"
                       "Carácter: muy cariñosa, juguetona y sociable con otros gatos.\n\n"
                       "Requisitos: hogar responsable, protección en ventanas, compromiso con su bienestar y controles "
                       "veterinarios.",
    },
    {
        "nombre": "Rocky",
        "imagen": "images/chiki.jpg",
        "autor": "Andrea",
        "especie": "perro",
        "raza": "Mestizo",
        "edad": "2 años",
        "sexo": "macho",
        "tamanio": "pequeño",
        "ubicacion": "Barranquilla, Atlántico",
        "descripcion": "Perrito mestizo de tamaño mini, noble y protector. Disfruta el aire libre y convive bien con "
                       "personas y otros animales.\n\n"
                       "Salud: vacunado, desparasitado y en excelente estado.\n\n"
                       "Carácter: noble, protector, juguetón y sociable con personas y otros animales.\n\n"
                       "Requisitos: espacio para jugar, paseos diarios, compromiso con su bienestar y controles "
                       "veterinarios.",
    },
]
