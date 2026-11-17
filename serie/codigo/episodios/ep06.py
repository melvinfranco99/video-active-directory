import math
from engine import *

CHAIN = [('n1', 220, 560, 'user', BLUE, "m.garcia", "Ventas · sin privilegios"),
         ('n2', 780, 640, 'users', VIOLET, "Soporte-N1", None),
         ('n3', 240, 850, 'users', VIOLET, "IT-Helpdesk", None),
         ('n4', 800, 940, 'pc', CYAN, "PC-IT-07", None),
         ('n5', 240, 1120, 'user', ORANGE, "adm.jperez", "Domain Admin"),
         ('n6', 800, 1220, 'crown', YELLOW, "Domain Admins", None)]
LINKS = [('n1', 'n2', "MemberOf", BLUE), ('n2', 'n3', "GenericAll", ORANGE), ('n3', 'n4', "AdminTo", CYAN),
         ('n4', 'n5', "HasSession", RED), ('n5', 'n6', "MemberOf", YELLOW)]

def chain(node_t, edge_t, cuts=None):
    nodes = [dict(id=i, x=x, y=y, r=50, icon=ic, col=c, t=node_t[k], label=l, sub=s) for k, (i, x, y, ic, c, l, s) in enumerate(CHAIN)]
    edges = []
    for k, (a, b, l, c) in enumerate(LINKS):
        e = dict(a=a, b=b, t=edge_t[k], col=c, label=l, ls=22)
        if cuts and k in cuts: e['cut'] = cuts[k]
        edges.append(e)
    return nodes, edges

n_s2, e_s2 = chain([0.3, 0.9, 2.5, 4.1, 5.7, 7.3], [0.9, 2.5, 4.1, 5.7, 7.3])
n_s5, e_s5 = chain([0.1] * 6, [0.2] * 5, cuts={1: 2.0, 3: 4.0})

ring = []
for i in range(10):
    a = -math.pi / 2 + i * 2 * math.pi / 10
    ring.append(dict(id=f'r{i}', x=540 + math.cos(a) * 330, y=900 + math.sin(a) * 330, r=34,
                     icon=['user', 'pc', 'users', 'server', 'user', 'pc', 'users', 'user', 'server', 'pc'][i],
                     col=[BLUE, CYAN, VIOLET, CYAN, BLUE, CYAN, VIOLET, BLUE, CYAN, CYAN][i], t=0.3 + i * 0.08))

SPEC = dict(
    ep="06", level="AVANZADO", icon='graph', transpose=1,
    title=["RUTAS DE ATAQUE", "Y AD CS"],
    subtitle="Piensa como el atacante: en grafos",
    scenes=[
        dict(title="Listas vs. grafos", dur=8, captions=[
            (0, "La seguridad de AD no es una lista de cuentas"),
            (4.0, f"Es una {cy('red de relaciones')} que se puede recorrer")],
            items=[dict(type='big', t=0.2, icon='graph', col=VIOLET, y=900, size=50,
                        text=f"«Los defensores piensan en {cy('listas')}.\nLos atacantes, en {pk('grafos')}.»",
                        sub="— John Lambert, Microsoft")]),
        dict(title="Una ruta real", dur=13, captions=[
            (0, f"Un usuario de Ventas {cy('sin privilegios')}…"),
            (2.5, f"…con un {ye('permiso olvidado')} sobre otro grupo…"),
            (5.7, f"…llega a un PC donde un {rd('Domain Admin')} tiene sesión…"),
            (8.4, f"…y en {rd('5 saltos')} controla el dominio")],
            items=[dict(type='graph', nodes=n_s2, edges=e_s2, highlights=[dict(node='n6', t0=8.0, t1=12.7, col=RED)])]),
        dict(title="Las aristas peligrosas", dur=9.5, captions=[
            (0, f"Cada relación es una {ye('arista')} del grafo"),
            (4.8, f"Las {rd('ACL')} mal heredadas son las más difíciles de ver")],
            items=[dict(type='cards', y=480, h=184, gap=18, items=[
                dict(t=0.3, icon='users', col=BLUE, title="MemberOf", desc="Grupos anidados que heredan permisos sin que nadie lo note"),
                dict(t=1.2, icon='pc', col=CYAN, title="AdminTo", desc="Administrador local de un equipo"),
                dict(t=2.1, icon='eye', col=RED, title="HasSession", desc="Un admin con sesión abierta deja credenciales en memoria"),
                dict(t=3.0, icon='key', col=ORANGE, title="GenericAll · WriteDacl", desc="ACL con control total sobre otro objeto")])]),
        dict(title="BloodHound para defensores", dur=9, captions=[
            (0, f"{cy('BloodHound')} dibuja estas relaciones automáticamente"),
            (4.2, f"Úsalo tú {gr('antes que el atacante')}: busca rutas hacia el Tier 0")],
            items=[dict(type='graph', nodes=ring + [dict(id='da', x=540, y=900, r=74, icon='crown', col=YELLOW, t=0.2, label="Domain Admins")],
                edges=[*[dict(a=f'r{i}', b=f'r{(i + 1) % 10}', t=1.0 + i * 0.06, col=WHITE, alpha=0.25, arrow=False, w=3) for i in range(10)],
                       *[dict(a=f'r{i}', b='da', t=1.4 + i * 0.05, col=WHITE, alpha=0.2, w=3) for i in (0, 4, 7)],
                       dict(a='r5', b='r6', t=2.6, col=RED, w=6), dict(a='r6', b='r7', t=2.9, col=RED, w=6),
                       dict(a='r7', b='da', t=3.2, col=RED, w=6, flow=True)],
                highlights=[dict(node='r5', t0=2.5, t1=8.6, col=RED)],
                chips=[dict(t=4.2, x=540, y=1330, text="Recolecta con SharpHound · analiza en BloodHound", col=hx('5B21B6'), size=24)])]),
        dict(title="Corta las rutas", dur=10, captions=[
            (0, f"Defender = {gr('cortar aristas')}, no solo parchear"),
            (2.0, f"Quita la {ye('ACL GenericAll')} que nadie recordaba"),
            (4.0, f"Los {rd('Domain Admins')} no inician sesión en PCs normales"),
            (6.5, f"Sin ruta, el atacante {gr('se queda atascado')}")],
            items=[dict(type='graph', nodes=n_s5, edges=e_s5, highlights=[dict(node='n6', t0=6.5, t1=9.6, col=GREEN)],
                        badges=[dict(node='n6', kind='check', t=6.6)])]),
        dict(title="AD CS: la ruta olvidada", dur=10.5, captions=[
            (0, f"{cy('AD CS')} (los certificados de AD) es una ruta muy explotada"),
            (3.6, f"Una plantilla mal configurada = {rd('certificado de admin')} para cualquiera"),
            (6.8, f"Revisa las plantillas: familias {ye('ESC1, ESC8…')} con Locksmith o PSPKIAudit")],
            items=[dict(type='graph', nodes=[
                dict(id='u', x=220, y=620, r=56, icon='user', col=BLUE, t=0.2, label="Usuario normal"),
                dict(id='tpl', x=820, y=620, r=56, icon='doc', col=ORANGE, t=0.6, label="Plantilla vulnerable", sub="ESC1"),
                dict(id='crt', x=820, y=960, r=56, icon='cert', col=RED, t=2.2, label="Certificado", sub="a nombre de un admin"),
                dict(id='dc', x=220, y=960, r=62, icon='dc', col=VIOLET, t=0.4, label="DC", sub="acepta el certificado")],
                edges=[dict(a='u', b='tpl', t=0.9, col=ORANGE, label="solicita"), dict(a='tpl', b='crt', t=2.0, col=RED, label="emite")],
                packets=[dict(a='crt', b='dc', t0=3.4, t1=4.4, label="PKINIT", col=RED, size=22, hold=0.2)],
                badges=[dict(node='dc', kind='x', t=4.5)],
                chips=[dict(t=5.0, x=540, y=1200, text="El solicitante elige el nombre (SAN) + autenticación de cliente", col=hx('9A3412'), size=22),
                       dict(t=6.8, x=540, y=1300, text="Audita: Locksmith · PSPKIAudit", col=hx('065F46'), size=24, icon='search')])]),
    ],
    recap=[("Piensa en grafos", "AD es una red de relaciones"),
           ("Aristas peligrosas", "MemberOf, AdminTo, HasSession, ACL"),
           ("BloodHound como defensor", "Encuentra rutas al Tier 0 antes que nadie"),
           ("Revisa AD CS", "Plantilla vulnerable = admin instantáneo")],
    next=("SIGUIENTE · EP. 07", "Hardening experto de AD"),
)
