from engine import *

def term(lines, t=0.1, h=720):
    return dict(type='term', y=480, h=h, t=t, lines=lines, cps=36)

SPEC = dict(
    ep="03", level="INTERMEDIO", icon='search', transpose=-3,
    title=["AUDITORÍA", "BÁSICA DE AD"],
    subtitle="5 comprobaciones que todo dominio necesita",
    scenes=[
        dict(title="Checklist de auditoría", dur=7.5, captions=[
            (0, f"Una auditoría básica de AD empieza por {ye('5 preguntas')}"),
            (3.8, f"Solo necesitas {cy('PowerShell')} y el módulo {ye('ActiveDirectory')}")],
            items=[dict(type='cards', y=480, h=132, gap=18, ts=34, items=[
                dict(t=0.3, icon='crown', col=RED, title="¿Quién es administrador?"),
                dict(t=0.8, icon='clock', col=YELLOW, title="¿Hay cuentas olvidadas?"),
                dict(t=1.3, icon='key', col=ORANGE, title="¿Contraseñas que nunca caducan?"),
                dict(t=1.8, icon='lock', col=CYAN, title="¿La política de contraseñas es sólida?"),
                dict(t=2.3, icon='search', col=GREEN, title="¿Lo automatizo?")])]),
        dict(title="1 · ¿Quién es admin?", dur=10.5, captions=[
            (0, f"Lista los miembros de {ye('Domain Admins')}, incluidos grupos anidados"),
            (4.6, f"Revisa también {cy('Enterprise Admins')}, {cy('Schema Admins')} y {cy('Administrators')}"),
            (7.8, f"Cada cuenta de más es {rd('una puerta de más')}")],
            items=[term([(0.4, 'cmd', 'Get-ADGroupMember "Domain Admins" -Recursive | Select-Object Name'),
                         (2.6, 'head', 'Name'), (2.7, 'out', '----'), (2.9, 'out', 'Administrator'), (3.1, 'out', 'it.jlopez'),
                         (3.4, 'warn', 'svc_backup       # ¿cuenta de servicio como DA?'),
                         (3.8, 'warn', 'temp.consultor   # ¿sigue haciendo falta?')]),
                   dict(type='chip', t=4.6, x=540, y=1290, text="En un AD en español: «Admins. del dominio»", col=hx('1E40AF'), size=26)]),
        dict(title="2 · Cuentas olvidadas", dur=10.5, captions=[
            (0, f"Busca cuentas sin inicio de sesión en {ye('90 días')}"),
            (4.2, f"Exempleados con cuenta activa = {rd('acceso regalado')}"),
            (7.4, f"{gr('Deshabilita')} primero; elimina tras revisar")],
            items=[term([(0.4, 'cmd', 'Search-ADAccount -AccountInactive -TimeSpan 90.00:00:00 -UsersOnly | Select Name,LastLogonDate'),
                         (3.4, 'head', 'Name             LastLogonDate'), (3.5, 'out', '----             -------------'),
                         (3.7, 'warn', 'p.ramirez        03/02/2025'), (3.9, 'warn', 'becario.2024     15/09/2024'),
                         (4.1, 'warn', 'svc_old_ftp      11/06/2021'),
                         (6.6, 'note', '# Desactivar en vez de borrar:'),
                         (6.9, 'cmd', 'Disable-ADAccount -Identity p.ramirez')])]),
        dict(title="3 · Contraseñas eternas", dur=10.5, captions=[
            (0, f"Busca contraseñas que {ye('nunca caducan')}"),
            (4.4, f"Una clave de {rd('2016')} en una cuenta de servicio es un regalo para un atacante"),
            (7.8, f"Solución moderna: {gr('gMSA')} (lo vemos en el Ep. 07)")],
            items=[term([(0.4, 'cmd', "Get-ADUser -Filter 'PasswordNeverExpires -eq $true' -Properties PasswordLastSet | Select Name,PasswordLastSet"),
                         (3.8, 'head', 'Name            PasswordLastSet'), (3.9, 'out', '----            ---------------'),
                         (4.1, 'bad', 'svc_sql         14/03/2016'), (4.3, 'bad', 'Administrator   02/11/2018'),
                         (4.5, 'warn', 'scanner01       20/01/2022')])]),
        dict(title="4 · Política de contraseñas", dur=10, captions=[
            (0, "Revisa la política de contraseñas del dominio"),
            (3.6, f"Longitud 7 y {rd('sin bloqueo de cuenta')} = suspenso"),
            (6.6, f"Apunta a {gr('≥ 14 caracteres')}, bloqueo y {cy('políticas específicas (FGPP)')} para admins")],
            items=[term([(0.4, 'cmd', 'Get-ADDefaultDomainPasswordPolicy'),
                         (1.7, 'good', 'ComplexityEnabled    : True'), (1.9, 'out', 'LockoutDuration      : 00:10:00'),
                         (2.1, 'bad', 'LockoutThreshold     : 0'), (2.3, 'out', 'MaxPasswordAge       : 42.00:00:00'),
                         (2.5, 'bad', 'MinPasswordLength    : 7'), (2.7, 'good', 'PasswordHistoryCount : 24')]),
                   dict(type='chip', t=3.6, x=540, y=1290, text="LockoutThreshold 0 = intentos ilimitados", col=hx('991B1B'), size=26)]),
        dict(title="5 · Automatiza", dur=9, captions=[
            (0, f"Herramientas {gr('gratuitas')} que revisan cientos de puntos"),
            (4.6, f"Úsalas {ye('con autorización')} y repite la auditoría cada trimestre")],
            items=[dict(type='cards', y=500, h=230, gap=26, items=[
                dict(t=0.3, icon='shield', col=GREEN, title="PingCastle", desc="Puntuación de riesgo del dominio en minutos"),
                dict(t=1.3, icon='search', col=VIOLET, title="Purple Knight", desc="Indicadores de exposición y de compromiso"),
                dict(t=2.3, icon='graph', col=RED, title="BloodHound", desc="Rutas de ataque hacia Domain Admins (Ep. 06)")])]),
    ],
    recap=[("Revisa los grupos privilegiados", "Domain/Enterprise/Schema Admins y Administrators"),
           ("Deshabilita cuentas inactivas", "Más de 90 días sin inicio de sesión"),
           ("Caza contraseñas eternas", "Sobre todo en cuentas de servicio"),
           ("Política sólida + herramientas", "≥ 14 caracteres, bloqueo y PingCastle")],
    next=("SIGUIENTE · EP. 04", "Eventos que debes vigilar"),
)
