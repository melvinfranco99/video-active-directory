from engine import *

SPEC = dict(
    ep="04", level="INTERMEDIO", icon='eye', transpose=4,
    title=["EVENTOS QUE", "DEBES VIGILAR"],
    subtitle="Los Event ID que delatan un ataque a AD",
    scenes=[
        dict(title="Sin registros no hay detección", dur=8.5, captions=[
            (0, f"Paso 0: activa la {ye('directiva de auditoría avanzada')} en los DC"),
            (4.2, f"Y envía los eventos a un {cy('SIEM')} central")],
            items=[dict(type='graph', nodes=[
                *[dict(id=f'dc{i}', x=210, y=600 + i * 280, r=54, icon='dc', col=VIOLET, t=0.3 + i * 0.2, label=f"DC0{i + 1}") for i in range(3)],
                dict(id='siem', x=780, y=880, r=84, icon='siem', col=CYAN, t=1.2, label="SIEM", sub="correlación + alertas"),
                dict(id='soc', x=780, y=1250, r=50, icon='eye', col=PINK, t=2.6, label="Equipo SOC", lp='l')],
                edges=[*[dict(a=f'dc{i}', b='siem', t=1.5 + i * 0.15, col=CYAN, flow=True) for i in range(3)],
                       dict(a='siem', b='soc', t=2.9, col=PINK, flow=True)],
                chips=[dict(t=0.6, x=700, y=560, text="Auditoría avanzada", col=hx('92400E'), size=24, icon='gear')])]),
        dict(title="Inicios de sesión", dur=10, captions=[
            (0, "Los inicios de sesión cuentan la historia"),
            (3.6, f"Picos de {rd('4625')} o {rd('4771')} = alguien probando contraseñas"),
            (7.0, f"{ye('4740')}: bloqueos en cadena delatan un ataque")],
            items=[dict(type='events', y=480, rows=[
                (0.4, '4624', 'Inicio de sesión correcto', 'ok'),
                (0.7, '4625', 'Error de inicio de sesión', 'warn'),
                (1.0, '4740', 'Cuenta de usuario bloqueada', 'warn'),
                (1.3, '4771', 'Error en la preautenticación Kerberos', 'warn')],
                highlights=[(1, 3.6, 9.7, RED), (3, 3.6, 7.0, RED), (2, 7.0, 9.7, YELLOW)]),
                dict(type='chip', t=3.8, x=540, y=1160, text="Muchos fallos desde un origen → spraying o fuerza bruta", col=hx('991B1B'), size=24)]),
        dict(title="Cuentas y grupos", dur=10, captions=[
            (0, f"Vigila altas y cambios en {cy('cuentas')} y {cy('grupos')}"),
            (3.8, f"{rd('4728')} en Domain Admins fuera de un cambio aprobado = {rd('incidente')}")],
            items=[dict(type='events', y=480, rh=104, rows=[
                (0.4, '4720', 'Se creó una cuenta de usuario', 'info'),
                (0.7, '4738', 'Se modificó una cuenta de usuario', 'info'),
                (1.0, '4728', 'Miembro añadido a grupo <b>global</b> de seguridad', 'crit'),
                (1.3, '4732', 'Miembro añadido a grupo <b>local</b> de seguridad', 'warn'),
                (1.6, '4756', 'Miembro añadido a grupo <b>universal</b> de seguridad', 'warn')],
                highlights=[(2, 3.8, 9.7, RED)]),
                dict(type='chip', t=4.0, x=540, y=1240, text="¿Alguien entró en Domain Admins? → alerta inmediata", col=hx('991B1B'), size=24)]),
        dict(title="Kerberos deja huella", dur=9.5, captions=[
            (0, f"Cada ticket Kerberos deja huella: {cy('4768')} y {cy('4769')}"),
            (3.4, f"Ráfagas de {ye('4769 con RC4')} delatan Kerberoasting (Ep. 05)")],
            items=[dict(type='events', y=480, rows=[
                (0.4, '4768', 'Se solicitó un TGT', 'info'),
                (0.7, '4769', 'Se solicitó un ticket de servicio', 'info'),
                (1.0, '4770', 'Se renovó un ticket de servicio', 'info')],
                highlights=[(1, 3.2, 9.2, ORANGE)]),
                dict(type='chip', t=3.4, x=540, y=1040, text="Tipo de cifrado del ticket: 0x17 = RC4", col=hx('9A3412'), size=26),
                dict(type='chip', t=4.4, x=540, y=1140, text="Muchos 4769 RC4 de una cuenta → posible Kerberoasting", col=hx('991B1B'), size=24)]),
        dict(title="Señales críticas", dur=10, captions=[
            (0, "Estos eventos merecen una alerta propia"),
            (3.0, f"{rd('4662')} con derechos de replicación fuera de un DC = {rd('DCSync')}"),
            (6.3, f"{rd('1102')}: borrar los registros nunca es buena señal")],
            items=[dict(type='events', y=480, rows=[
                (0.4, '4672', 'Privilegios especiales asignados al iniciar sesión', 'warn'),
                (0.7, '4662', 'Operación en objeto: replicación del directorio', 'crit'),
                (1.0, '5136', 'Se modificó un objeto del directorio (GPO, ACL…)', 'warn'),
                (1.3, '1102', 'Se borró el registro de auditoría', 'crit')],
                highlights=[(1, 3.0, 6.3, RED), (3, 6.3, 9.7, RED)]),
                dict(type='chip', t=3.1, t1=6.2, x=540, y=1160, text="4662 + GUID de replicación desde un no-DC", col=hx('991B1B'), size=24),
                dict(type='chip', t=6.4, x=540, y=1160, text="1102 = alguien borró las pruebas", col=hx('991B1B'), size=26)]),
        dict(title="Truco profesional", dur=8.5, captions=[
            (0, f"Más eventos no es más seguridad: {ye('menos ruido')}, mejores alertas"),
            (4.4, f"Empieza por los {cy('DC')} y las {cy('cuentas privilegiadas')}")],
            items=[dict(type='cards', y=500, h=230, gap=26, items=[
                dict(t=0.3, icon='clock', col=CYAN, title="Crea una línea base", desc="¿Qué es normal en tu red? Así verás lo raro"),
                dict(t=1.3, icon='graph', col=VIOLET, title="Correlaciona", desc="Cuenta + origen + hora + tipo de evento"),
                dict(t=2.3, icon='bolt', col=ORANGE, title="Prioriza alertas", desc="Grupos privilegiados y DC primero")])]),
    ],
    recap=[("Auditoría avanzada + SIEM", "Sin logs centralizados no hay detección"),
           ("4625 · 4771 · 4740", "Contraseñas probadas y bloqueos"),
           ("4728 · 4732 · 4756", "Cambios en grupos privilegiados"),
           ("4769 RC4 · 4662 · 1102", "Kerberoasting, DCSync y borrado de logs")],
    next=("SIGUIENTE · EP. 05", "Ataques comunes a AD"),
)
