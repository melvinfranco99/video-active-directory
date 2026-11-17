from engine import *

SPEC = dict(
    ep="01", level="BÁSICO", icon='domain',
    title=["¿QUÉ ES", "ACTIVE DIRECTORY?"],
    subtitle="El cerebro de la red corporativa",
    scenes=[
        dict(title="El problema", dur=7, captions=[
            (0, "Imagina una empresa con cientos de equipos y personas"),
            (3.0, f"Cuentas sueltas en cada PC = {rd('caos')} y cero control")],
            items=[dict(type='graph', nodes=[
                dict(id=f'p{i}', x=[240, 540, 840][i % 3], y=[650, 980][i // 3], icon='pc', col=BLUE, t=0.3 + i * 0.15,
                     label=f"PC-0{i + 1}", sub=["admin / 1234", "local / Pass1", "jose / jose", "admin / admin", "user / 2020", "¿? / ¿?"][i])
                for i in range(6)],
                badges=[dict(node=f'p{i}', kind='x', t=3.0 + i * 0.15) for i in range(6)],
                chips=[dict(t=3.9, x=540, y=1270, text="Contraseñas por todas partes · cero control", col=hx('B91C1C'), size=26)])]),
        dict(title="La solución: un directorio", dur=8, captions=[
            (0, f"{cy('Active Directory')} guarda todas las identidades en un servidor: el {ye('DC')}"),
            (4.0, f"Un usuario y una contraseña para {gr('toda la red')}")],
            items=[dict(type='graph', nodes=[
                dict(id='dc', x=540, y=900, r=88, icon='dc', col=VIOLET, t=0.2, label="Controlador de dominio", sub="DC · servicio AD DS"),
                dict(id='u', x=540, y=580, r=56, icon='users', col=CYAN, t=0.6, label="Empleados", lp='r'),
                *[dict(id=f'p{i}', x=x, y=y, icon=ic, col=BLUE, t=1.0 + i * 0.12, r=50)
                  for i, (x, y, ic) in enumerate([(170, 640, 'pc'), (910, 640, 'server'), (150, 980, 'pc'), (930, 980, 'pc'), (300, 1260, 'server'), (780, 1260, 'pc')])]],
                edges=[dict(a='u', b='dc', t=0.9, col=CYAN, label="1 sola cuenta"),
                       *[dict(a='dc', b=f'p{i}', t=1.3 + i * 0.12, col=VIOLET, flow=True, arrow=False) for i in range(6)]],
                badges=[dict(node=f'p{i}', kind='check', t=4.0 + i * 0.12) for i in range(6)])]),
        dict(title="¿Qué guarda AD?", dur=8.5, captions=[
            (0, f"Todo en AD es un {cy('objeto')} con atributos"),
            (4.4, f"Las {ye('OU')} ordenan; los {cy('grupos')} dan permisos")],
            items=[dict(type='cards', y=480, h=196, gap=22, items=[
                dict(t=0.3, icon='user', col=CYAN, title="Usuarios", desc="Personas y cuentas de servicio que inician sesión"),
                dict(t=1.3, icon='users', col=VIOLET, title="Grupos", desc="Dan permisos a muchos usuarios a la vez"),
                dict(t=2.3, icon='pc', col=BLUE, title="Equipos", desc="PCs y servidores unidos al dominio"),
                dict(t=3.3, icon='ou', col=YELLOW, title="Unidades organizativas (OU)", desc="Carpetas para ordenar objetos y aplicar políticas")])]),
        dict(title="Cómo se organiza", dur=9.5, captions=[
            (0, f"{pk('Bosque')} → {cy('dominios')} → {ye('OU')} → objetos"),
            (4.6, f"El {pk('bosque')}, no el dominio, es la {rd('frontera de seguridad')}")],
            items=[dict(type='graph',
                zones=[dict(x=60, y=470, w=960, h=900, t=0.1, label="BOSQUE", sub="frontera de seguridad", col=PINK)],
                nodes=[
                    dict(id='root', x=540, y=630, icon='domain', col=CYAN, t=0.5, label="empresa.local", sub="Dominio raíz", lp='r'),
                    dict(id='ven', x=230, y=900, icon='ou', col=YELLOW, t=1.3, r=52, label="OU Ventas"),
                    dict(id='it', x=540, y=900, icon='ou', col=YELLOW, t=1.5, r=52, label="OU IT"),
                    dict(id='mx', x=850, y=900, icon='domain', col=CYAN, t=2.6, r=52, label="mx.empresa.local", sub="Dominio hijo"),
                    dict(id='ana', x=150, y=1200, icon='user', col=BLUE, t=2.0, r=46, label="Ana"),
                    dict(id='pc', x=330, y=1200, icon='pc', col=BLUE, t=2.15, r=46, label="PC-VEN-01"),
                    dict(id='sop', x=540, y=1200, icon='users', col=VIOLET, t=2.3, r=46, label="Soporte"),
                ],
                edges=[dict(a='root', b='ven', t=1.1), dict(a='root', b='it', t=1.3),
                       dict(a='ven', b='ana', t=1.8), dict(a='ven', b='pc', t=1.95), dict(a='it', b='sop', t=2.1),
                       dict(a='root', b='mx', t=2.9, col=CYAN, dashed=True, flow=True, label="Confianza", lpos=0.55, ldx=30)],
                highlights=[dict(node='mx', t0=4.6, t1=8.8, col=PINK), dict(node='root', t0=4.6, t1=8.8, col=PINK)])]),
        dict(title="Directivas de grupo (GPO)", dur=8.5, captions=[
            (0, f"Una {ye('GPO')} es un paquete de configuración"),
            (4.2, f"Se aplica sola a {gr('todos los equipos')} de la OU, sin ir uno a uno")],
            items=[dict(type='graph', nodes=[
                dict(id='gpo', x=700, y=600, icon='gpo', col=YELLOW, t=0.3, label="GPO «Seguridad PCs»", lp='r', ls=24),
                dict(id='ou', x=700, y=880, icon='ou', col=YELLOW, t=0.8, r=52, label="OU Ventas", lp='r'),
                *[dict(id=f'p{i}', x=[240, 540, 840][i], y=1180, icon='pc', col=BLUE, t=1.4 + i * 0.12, r=50, label=f"PC-VEN-0{i + 1}") for i in range(3)]],
                edges=[dict(a='gpo', b='ou', t=1.0, col=YELLOW, label="vinculada", ldx=-90),
                       *[dict(a='ou', b=f'p{i}', t=1.6 + i * 0.12, col=YELLOW, alpha=0.5) for i in range(3)]],
                packets=[dict(a='ou', b=f'p{i}', t0=4.3 + i * 0.2, t1=5.1 + i * 0.2, label="GPO", col=YELLOW, size=22) for i in range(3)],
                badges=[dict(node=f'p{i}', kind='check', t=5.2 + i * 0.2) for i in range(3)],
                chips=[dict(t=2.2, x=270, y=600, text="Bloqueo a los 10 min", col=hx('92400E'), size=24, icon='lock'),
                       dict(t=2.6, x=270, y=690, text="Contraseña ≥ 14 caract.", col=hx('92400E'), size=24),
                       dict(t=3.0, x=270, y=780, text="USB bloqueado", col=hx('92400E'), size=24)])]),
        dict(title="¿Por qué protegerlo?", dur=7, captions=[
            (0, f"Por eso AD es el {rd('objetivo nº 1')} de los atacantes"),
            (3.6, f"En esta serie aprenderás a {gr('auditarlo y defenderlo')}")],
            items=[dict(type='big', t=0.2, icon='crown', col=YELLOW, y=930, size=70,
                        text=f"Quien controla AD,\n{ye('controla la empresa')}",
                        sub="Cuentas · equipos · servidores · correo · accesos")]),
    ],
    recap=[("AD = directorio central de identidades", "Lo ejecutan los controladores de dominio (DC)"),
           ("Objetos: usuarios, grupos, equipos, OU", "Cada uno con atributos y permisos"),
           ("Bosque → dominios → OU", "El bosque es la frontera de seguridad"),
           ("GPO = configuración masiva", "Se vinculan a sitios, dominios u OU")],
    next=("SIGUIENTE · EP. 02", "Kerberos: así inicias sesión"),
)
