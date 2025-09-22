
from flask import Flask, request, jsonify, redirect, render_template, url_for
from Config.db import app

# Página de detalle de cachorro
@app.route("/cachorro")
def Pagina2_Cachorro():
    return render_template("Pagina2_Cachorro.html")

# Formulario de adopción
@app.route("/formulario", methods=["GET", "POST"])
def Formulario_Para_Adoptar():
    if request.method == "POST":
        # Aquí podrías procesar y guardar la solicitud de adopción.
        # Por ahora, redirigimos a la página del cachorro como confirmación sencilla.
        return redirect("/cachorro")
    return render_template("Formulario_Para_Adoptar.html")



# Home
@app.route("/")
def Pagina_Principal():
    return render_template("Pagina_Principal.html")


# Registro usuario

@app.route("/registro", methods=["GET", "POST"])
def Registro_Usuario():
    if request.method == "POST":
        # Aquí podrías validar/guardar datos. Por ahora solo redirigimos.
        return redirect("/iniciar-sesion")
    return render_template("Registro_Usuario.html")


@app.route("/iniciar-sesion", methods=["GET", "POST"])
def Iniciar_Sesion():
    if request.method == "POST":
        # Aquí podrías validar credenciales; por ahora redirigimos al inicio
        return redirect("/")
    return render_template("Iniciar_Sesion.html")

# Registro administrador
@app.route("/registro-administrador", methods=["GET", "POST"])
def Registro_Administrador():
    if request.method == "POST":
        # Aquí podrías validar/guardar datos de administrador
        return redirect("/iniciar-sesion")
    return render_template("Registro_Administrador.html")

# Listado de adopción / Mascotas
@app.route("/adopcion")
def Pagina_Adopcion():
    return render_template("Pagina1_Adopcion.html")

# Alias para compatibilidad: /mascotas -> /adopcion
@app.route("/mascotas")
def Mascotas_Alias():
    return redirect("/adopcion")

# Fundaciones
@app.route("/fundaciones")
def Pagina_Fundacion():
    return render_template("Pagina_Fundacion.html")

# Página específica de la fundación Funcuan
@app.route("/funcuan")
def Pagina_Funcuan():
    # reutilizamos la plantilla de fundación por ahora; si luego hay varias, podemos parametrizar
    return render_template("Pagina_Fundacion.html")

# Página para postular mascotas
@app.route("/postular", methods=["GET", "POST"])
def Postular_Mascotas():
    if request.method == "POST":
        # Aquí podrías procesar y guardar la postulación de mascota
        return redirect("/adopcion")
    return render_template("Postular_Mascotas.html")


if __name__ == "__main__":
    app.run(debug=True, port=5100, host="0.0.0.0")
