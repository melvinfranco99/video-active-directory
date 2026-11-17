from engine import *

def tier(k, y, col, label, sub, items, t0):
    nodes = [dict(id=f't{k}{i}', x=[250, 540, 830][i], y=y + 120, r=44, icon=ic, col=col, t=t0 + 0.2 + i * 0.12, label=l, ls=22)
             for i, (ic, l) in enumerate(items)]
    zone = dict(x=60, y=y, w=960, h=262, t=t0, label=label, sub=sub, col=col)
    return zone, nodes

z0, n0 = tier(0, 470, RED, "TIER 0 · Identidad", "lo más crítico", [('dc', "DCs"), ('cert', "AD CS"), ('cloud', "Entra Connect")], 0.2)
z1, n1 = tier(1, 752, ORANGE, "TIER 1 · Servidores", "apps y datos", [('server', "SQL"), ('gear', "Apps"), ('server', "Archivos")], 0.8)
z2, n2 = tier(2, 1034, CYAN, "TIER 2 · Puestos", "usuarios", [('pc', "Estaciones"), ('user', "Usuarios"), ('users', "Soporte")], 1.4)

CHECK = ["Modelo por niveles + PAW", "Protected Users para admins", "LAPS en todos los equipos", "gMSA para servicios",
         "Sin SMBv1 · NTLMv1 · RC4", "Firma LDAP y SMB obligatoria", "krbtgt rotada", "Plantillas AD CS revisadas"]

SPEC = dict(
    ep="07", level="EXPERTO", icon='shield', transpose=-2,
    title=["HARDENING", "EXPERTO DE AD"],
    subtitle="Cómo blindar un dominio de verdad",
    scenes=[
        dict(title="Modelo por niveles", dur=11, captions=[
            (0, f"Separa la administración en {ye('niveles')}"),
            (3.0, f"{rd('Tier 0')} = lo que controla la identidad: DC, AD CS, sincronización"),
            (5.6, f"Una credencial de Tier 0 {rd('nunca')} toca un nivel inferior"),
            (8.4, f"Evolución actual: {cy('Enterprise Access Model')} de Microsoft")],
            items=[dict(type='graph', zones=[z0, z1, z2], nodes=n0 + n1 + n2,
                        edges=[dict(a='t00', b='t21', t=4.8, col=RED, w=5, label="login T0", ls=22, cut=5.7, lpos=0.62)])]),
        dict(title="Protege las credenciales", dur=10.5, captions=[
            (0, f"Que robar credenciales sea {ye('difícil')}…"),
            (5.2, f"…y que las robadas {gr('caduquen o no sirvan')}")],
            items=[dict(type='cards', y=480, h=184, gap=18, items=[
                dict(t=0.3, icon='shield', col=VIOLET, title="Protected Users", desc="Sin NTLM, sin delegación, sin RC4; TGT de 4 h"),
                dict(t=1.3, icon='key', col=CYAN, title="Windows LAPS", desc="Contraseña de admin local única y rotada en cada equipo"),
                dict(t=2.3, icon='lock', col=GREEN, title="Credential Guard", desc="Aísla los secretos de LSASS con virtualización"),
                dict(t=3.3, icon='server', col=ORANGE, title="gMSA", desc="Cuentas de servicio con contraseñas largas que rotan solas")])]),
        dict(title="Protocolos", dur=10, captions=[
            (0, f"Cierra los protocolos {rd('heredados')}"),
            (4.8, f"Audita {ye('antes')} de bloquear: descubre qué se rompería")],
            items=[dict(type='compare', y=500, t=0.2,
                        left=("DESACTIVA", RED, [(0.6, "SMBv1"), (1.1, "NTLMv1 y hashes LM"), (1.6, "RC4 en Kerberos"), (2.1, "Print Spooler en los DC")], 'x'),
                        right=("EXIGE", GREEN, [(2.7, "Firma SMB"), (3.2, "Firma LDAP + channel binding"), (3.7, "AES en Kerberos"), (4.2, "Auditoría del uso de NTLM")], 'check'))]),
        dict(title="Las joyas de la corona", dur=10.5, captions=[
            (0, f"Protege lo que da {rd('persistencia')} al atacante"),
            (5.2, f"Rotar {ye('krbtgt')} dos veces invalida los Golden Tickets")],
            items=[dict(type='cards', y=480, h=184, gap=18, items=[
                dict(t=0.3, icon='key', col=RED, title="Rota krbtgt dos veces", desc="Esperando replicación y la vida del TGT entre ambas", hl=5.2),
                dict(t=1.3, icon='users', col=ORANGE, title="AdminSDHolder", desc="Vigila su ACL: un clásico de persistencia"),
                dict(t=2.3, icon='dc', col=VIOLET, title="Contraseña DSRM", desc="Única por DC, custodiada y rotada"),
                dict(t=3.3, icon='gear', col=CYAN, title="Delegaciones Kerberos", desc="Elimina la delegación sin restricciones")])]),
        dict(title="Detecta y recupera", dur=10, captions=[
            (0, f"Asume que entrarán: {cy('detecta pronto')}"),
            (5.0, f"Y practica {gr('recuperar el bosque')} antes de necesitarlo")],
            items=[dict(type='cards', y=480, h=184, gap=18, items=[
                dict(t=0.3, icon='eye', col=PINK, title="Honeytokens", desc="Cuentas señuelo: si alguien las toca, alerta"),
                dict(t=1.3, icon='search', col=CYAN, title="ITDR", desc="Detección de amenazas de identidad (p. ej. Defender for Identity)"),
                dict(t=2.3, icon='layers', col=GREEN, title="Backups offline de AD", desc="Y un plan de recuperación del bosque probado"),
                dict(t=3.3, icon='bug', col=ORANGE, title="Simulacros", desc="Ejercicios de purple team, siempre autorizados")])]),
        dict(title="Checklist experto", dur=9.5, captions=[
            (0, f"Tu {ye('checklist')} de hardening de AD"),
            (5.0, f"Avanza paso a paso y {gr('mide tu progreso')} con PingCastle")],
            items=[dict(type='cards', y=480, h=96, gap=14, ts=31, items=[
                dict(t=0.2 + i * 0.5, icon='txt:' + str(i + 1), col=[CYAN, VIOLET, GREEN, ORANGE, RED, BLUE, YELLOW, PINK][i],
                     title=s, state=('check', 0.55 + i * 0.5)) for i, s in enumerate(CHECK)])]),
    ],
    recap=[("Modelo por niveles", "Tier 0 aislado y administrado desde PAW"),
           ("Credenciales blindadas", "Protected Users, LAPS, Credential Guard, gMSA"),
           ("Protocolos modernos", "Sin SMBv1, NTLMv1 ni RC4; con firmas"),
           ("Detecta y recupera", "Honeytokens, ITDR y backups offline")],
    next=("FIN DE LA SERIE", "Vuelve al Ep. 01 y compártela"),
)
