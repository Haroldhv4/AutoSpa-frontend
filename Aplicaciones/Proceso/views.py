from django.shortcuts import render,get_object_or_404,redirect
from django.contrib import messages
import requests
import json
from django.conf import settings
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from django.http import JsonResponse

# Load environment variables
load_dotenv()

def plantilla(request):
    return render(request,'plantilla.html')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

def login_view(request):
    if request.method == "POST":
        correo = request.POST.get("correo")
        password = request.POST.get("password")

        # Consultar Supabase
        url = f"{SUPABASE_URL}/rest/v1/usuario?correo=eq.{correo}&select=id_usuario,contraseña,tipo_usuario"
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200 and response.json():
            user = response.json()[0]
            if user["tipo_usuario"] == "Administrador" and user["contraseña"] == password:
                request.session["admin_id"] = user["id_usuario"]
                return redirect("dashboard")
            else:
                messages.error(request, "Credenciales incorrectas o no tienes permiso.")
        else:
            messages.error(request, "Usuario no encontrado.")
    
    return render(request, "login.html")


HEADERS = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json"
}

def dashboard_view(request):
    if not request.session.get("admin_id"):
        return redirect("login")
    try:
        # Obtener órdenes por estado
        estados = ['Pendiente', 'En Proceso', 'Finalizada']
        ordenes_por_estado = {}
        total_por_estado = {}

        for estado in estados:
            url = f"{SUPABASE_URL}/rest/v1/orden_trabajo?estado=eq.{estado}"
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 200:
                ordenes_por_estado[estado] = response.json()
                total_por_estado[estado] = len(response.json())
            else:
                print(f"Error al obtener órdenes para el estado {estado}:", response.text)
                ordenes_por_estado[estado] = []
                total_por_estado[estado] = 0

        # Obtener el total de órdenes de la semana y del mes
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())  # Lunes de esta semana
        start_of_month = today.replace(day=1)  # Primer día del mes

        url_week = f"{SUPABASE_URL}/rest/v1/orden_trabajo?select=id_orden&fecha_creacion=gte.{start_of_week.isoformat()}"
        url_month = f"{SUPABASE_URL}/rest/v1/orden_trabajo?select=id_orden&fecha_creacion=gte.{start_of_month.isoformat()}"

        week_response = requests.get(url_week, headers=HEADERS)
        month_response = requests.get(url_month, headers=HEADERS)

        week_data = len(week_response.json()) if week_response.status_code == 200 else 0
        month_data = len(month_response.json()) if month_response.status_code == 200 else 0

        # Obtener el total de cotizaciones de la semana y del mes
        url_week_cotizaciones = f"{SUPABASE_URL}/rest/v1/cotizacion?select=id_cotizacion&in_created=gte.{start_of_week.isoformat()}"
        url_month_cotizaciones = f"{SUPABASE_URL}/rest/v1/cotizacion?select=id_cotizacion&in_created=gte.{start_of_month.isoformat()}"

        week_response_cotizaciones = requests.get(url_week_cotizaciones, headers=HEADERS)
        month_response_cotizaciones = requests.get(url_month_cotizaciones, headers=HEADERS)

        week_data_cotizaciones = len(week_response_cotizaciones.json()) if week_response_cotizaciones.status_code == 200 else 0
        month_data_cotizaciones = len(month_response_cotizaciones.json()) if month_response_cotizaciones.status_code == 200 else 0

        # Obtener el total de usuarios registrados
        url_usuarios = f"{SUPABASE_URL}/rest/v1/auth.users?select=id"
        response_usuarios = requests.get(url_usuarios, headers=HEADERS)
        total_usuarios = len(response_usuarios.json()) if response_usuarios.status_code == 200 else 0

        context = {
            'ordenes_por_estado': ordenes_por_estado,
            'total_por_estado': total_por_estado,
            'week_data': week_data,
            'month_data': month_data,
            'week_data_cotizaciones': week_data_cotizaciones,
            'month_data_cotizaciones': month_data_cotizaciones,
            'total_usuarios': total_usuarios,
        }
        return render(request, 'dashboard.html', context)

    except requests.RequestException as e:
        print("Error en la solicitud:", e)
        messages.error(request, "No se pudieron obtener los datos.")
        return render(request, 'dashboard.html', {
            'ordenes_por_estado': {},
            'total_por_estado': {},
            'week_data': 0,
            'month_data': 0,
            'week_data_cotizaciones': 0,
            'month_data_cotizaciones': 0,
            'total_usuarios': 0,
        })
    
def logout_view(request):
    if "admin_id" in request.session:
        del request.session["admin_id"]
    return redirect("login")

def check_session_view(request):
    is_authenticated = "admin_id" in request.session
    return JsonResponse({"authenticated": is_authenticated})