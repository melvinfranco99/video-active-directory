from engine import *

def dm(det, mit, t=4.2):
    return dict(type='dm', t=t, y=1085, h=140, detect=det, mitigate=mit)

ATT = dict(id='att', icon='attacker', col=RED, r=60)
KDC = dict(id='kdc', x=830, y=640, r=62, icon='dc', col=VIOLET, label="KDC (DC)")

SPEC = dict(
    ep="05", level="AVANZADO", icon='attacker', transpose=-5, bpm=100,
    chords=[[45, 57, 60, 64, 67], [41, 57, 60, 65, 69], [48, 55, 60, 64, 67], [43, 55, 59, 62, 67]],
    title=["ATAQUES COMUNES", "A ACTIVE DIRECTORY"],
    subtitle="Cómo funcionan y cómo detectarlos",
    scenes=[
        dict(title="Password spraying", dur=9.5, captions=[
            (0, f"Una contraseña común contra {ye('muchos usuarios')}"),
            (3.0, f"Pocos intentos por cuenta: así esquiva el {rd('bloqueo')}")],
            items=[dict(type='graph', nodes=[
                dict(ATT, x=190, y=760, t=0.2, label="Atacante"),
                *[dict(id=f'u{i}', x=830, y=520 + i * 122, r=40, icon='user', col=BLUE, t=0.4 + i * 0.1, label=n, lp='r', ls=22)
                  for i, n in enumerate(["ana", "luis", "marta", "pedro", "sara"])]],
                edges=[dict(a='att', b=f'u{i}', t=0.7 + i * 0.1, col=RED, alpha=0.35, arrow=False) for i in range(5)],
                packets=[dict(a='att', b=f'u{i}', t0=1.0 + i * 0.25, t1=1.8 + i * 0.25, label="Verano2026!", col=RED, size=20, hold=0.1) for i in range(5)],
                badges=[dict(node=f'u{i}', kind='x' if i != 3 else 'warn', t=1.9 + i * 0.25) for i in range(5)],
                highlights=[dict(node='u3', t0=2.9, t1=9.0, col=RED)])]
                + [dm("Muchos 4625/4771 desde un origen, cada uno contra un usuario distinto",
                      "Contraseñas largas, bloqueo de contraseñas comunes y MFA")]),
        dict(title="Kerberoasting", dur=10, captions=[
            (0, f"Cualquier usuario puede pedir tickets de servicios con {ye('SPN')}"),
            (3.3, f"El ticket se crackea {rd('offline')} y revela la contraseña del servicio")],
            items=[dict(type='graph', nodes=[
                dict(ATT, x=200, y=640, t=0.2, label="Usuario del dominio", sub="sin privilegios", col=ORANGE),
                dict(KDC, t=0.4),
                dict(id='crk', x=520, y=900, r=56, icon='bolt', col=RED, t=3.3, label="Crackeo offline", sub="sin tocar la red")],
                edges=[dict(a='att', b='crk', t=3.4, col=RED, dashed=True)],
                packets=[dict(a='att', b='kdc', t0=0.8, t1=1.9, label="TGS-REQ · svc_sql", col=YELLOW, curve=-70, size=22),
                         dict(a='kdc', b='att', t0=2.1, t1=3.2, label="Ticket RC4", col=ORANGE, curve=-70, icon='ticket', size=22)],
                badges=[dict(node='crk', kind='key', t=4.0)])]
                + [dm("4769 con cifrado RC4 (0x17) en ráfaga desde una cuenta",
                      "gMSA o contraseñas de 25+ caracteres y solo AES", 4.6)]),
        dict(title="AS-REP Roasting", dur=9.5, captions=[
            (0, f"Cuentas con la {ye('preautenticación Kerberos desactivada')}"),
            (3.3, f"El KDC entrega datos {rd('crackeables')} a cualquiera que pregunte")],
            items=[dict(type='graph', nodes=[
                dict(ATT, x=200, y=640, t=0.2, label="Atacante"),
                dict(KDC, t=0.4),
                dict(id='acc', x=520, y=920, r=54, icon='user', col=ORANGE, t=0.6, label="svc_legacy", sub="«No pedir preautenticación»")],
                edges=[dict(a='kdc', b='acc', t=0.8, col=ORANGE, alpha=0.4, dashed=True, arrow=False)],
                packets=[dict(a='att', b='kdc', t0=0.9, t1=2.0, label="AS-REQ sin prueba", col=YELLOW, curve=-70, size=22),
                         dict(a='kdc', b='att', t0=2.2, t1=3.3, label="AS-REP crackeable", col=RED, curve=-70, size=22)],
                highlights=[dict(node='acc', t0=0.7, t1=9.0, col=ORANGE)])]
                + [dm("4768 con tipo de preautenticación 0",
                      "Quita «No pedir preautenticación Kerberos» de todas las cuentas")]),
        dict(title="Pass-the-Hash", dur=9.5, captions=[
            (0, f"El atacante roba el {ye('hash NTLM')} de una sesión abierta"),
            (3.2, f"Y lo usa {rd('como si fuera la contraseña')}")],
            items=[dict(type='graph', nodes=[
                dict(id='pc', x=200, y=640, r=58, icon='pc', col=BLUE, t=0.2, label="PC comprometido"),
                dict(id='h', x=520, y=900, r=56, icon='hash', col=RED, t=1.0, label="Hash NTLM", sub="extraído de la memoria (LSASS)"),
                dict(id='srv', x=840, y=640, r=58, icon='server', col=CYAN, t=0.4, label="Servidor")],
                edges=[dict(a='pc', b='h', t=1.1, col=RED, dashed=True)],
                packets=[dict(a='h', b='srv', t0=2.2, t1=3.2, label="Hash, sin contraseña", col=RED, size=22)],
                badges=[dict(node='pc', kind='x', t=0.6), dict(node='srv', kind='x', t=3.3)])]
                + [dm("4624 tipo 3 con NTLM desde orígenes inusuales",
                      "LAPS, Credential Guard y admins de dominio fuera de los PC")]),
        dict(title="DCSync", dur=9.5, captions=[
            (0, f"El atacante {ye('se hace pasar por un DC')}"),
            (3.2, f"Y el DC le entrega {rd('todos los hashes')}, incluido krbtgt")],
            items=[dict(type='graph', nodes=[
                dict(ATT, x=200, y=680, t=0.2, label="Cuenta con derechos", sub="de replicación"),
                dict(id='dc', x=830, y=680, r=66, icon='dc', col=VIOLET, t=0.4, label="DC")],
                packets=[dict(a='att', b='dc', t0=0.8, t1=1.9, label="¿Me replicas?", col=YELLOW, curve=-80, size=22),
                         dict(a='dc', b='att', t0=2.2, t1=3.2, label="Todos los hashes", col=RED, curve=-80, icon='hash', size=22, hold=0.3)],
                badges=[dict(node='att', kind='key', t=3.3)],
                chips=[dict(t=3.5, x=520, y=940, text="incluido el de krbtgt", col=hx('991B1B'), size=26, icon='key')])]
                + [dm("4662 con GUID de replicación desde una cuenta que no es DC",
                      "Audita quién tiene «Replicating Directory Changes All»")]),
        dict(title="Golden Ticket", dur=10, captions=[
            (0, f"Con la clave de {ye('krbtgt')} se fabrican TGT a medida"),
            (3.3, f"{rd('Acceso total')} y persistente a todo el dominio")],
            items=[dict(type='graph', nodes=[
                dict(id='k', x=170, y=720, r=56, icon='key', col=YELLOW, t=0.2, label="Hash de krbtgt"),
                dict(id='tgt', x=500, y=720, r=62, icon='ticket', col=RED, t=0.9, label="TGT falsificado", sub="cualquier usuario y grupo"),
                *[dict(id=f't{i}', x=880, y=540 + i * 190, r=44, icon=ic, col=CYAN, t=1.8 + i * 0.15) for i, ic in enumerate(['dc', 'server', 'pc'])]],
                edges=[dict(a='k', b='tgt', t=0.7, col=YELLOW, label="firma"),
                       *[dict(a='tgt', b=f't{i}', t=2.0 + i * 0.15, col=RED, flow=True) for i in range(3)]],
                badges=[dict(node='tgt', kind='crown', t=2.8), *[dict(node=f't{i}', kind='x', t=2.6 + i * 0.15) for i in range(3)]])]
                + [dm("Tickets con vida anómala y 4769 sin un 4768 previo",
                      "Rota krbtgt dos veces y aísla el Tier 0", 4.3)]),
    ],
    recap=[("Spraying y Kerberoasting", "Contraseñas débiles = puerta de entrada"),
           ("AS-REP Roasting", "Nunca desactives la preautenticación"),
           ("Pass-the-Hash", "Protege las credenciales en memoria"),
           ("DCSync y Golden Ticket", "Fin de la partida: protege el Tier 0")],
    next=("SIGUIENTE · EP. 06", "Rutas de ataque y AD CS"),
)
