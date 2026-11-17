from engine import *

def base(extra_nodes=(), dim_srv=False):
    return [dict(id='pc', x=220, y=920, r=62, icon='pc', col=BLUE, t=0.1, label="Tu PC", sub="usuaria: Ana"),
            dict(id='kdc', x=820, y=640, r=66, icon='dc', col=VIOLET, t=0.25, label="KDC", sub="en el DC"),
            dict(id='srv', x=820, y=1190, r=58, icon='server', col=CYAN, t=0.4, label="Servidor de archivos", sub="SPN: cifs/files01")]

FAINT = [dict(a='pc', b='kdc', t=0.3, alpha=0.18, arrow=False, dashed=True),
         dict(a='pc', b='srv', t=0.4, alpha=0.18, arrow=False, dashed=True)]

SPEC = dict(
    ep="02", level="BÁSICO", icon='ticket', transpose=2,
    title=["KERBEROS:", "ASÍ INICIAS SESIÓN"],
    subtitle="El protocolo que protege (y expone) a AD",
    scenes=[
        dict(title="La analogía del festival", dur=8, captions=[
            (0, f"{cy('Kerberos')} funciona como un festival"),
            (4.0, f"Primero la {pk('pulsera')}, luego una {cy('entrada')} por atracción")],
            items=[dict(type='cards', y=500, h=230, gap=26, items=[
                dict(t=0.3, icon='ticket', col=PINK, title="Pulsera = TGT", desc="Demuestra quién eres. La recibes al iniciar sesión (válida ~10 h)"),
                dict(t=1.4, icon='ticket', col=CYAN, title="Entrada = ticket de servicio", desc="Acceso a una atracción concreta: un servidor o servicio"),
                dict(t=2.5, icon='dc', col=VIOLET, title="Taquilla = KDC", desc="El controlador de dominio emite las dos")])]),
        dict(title="1 · Pides el TGT", dur=9, captions=[
            (0, f"Tu PC envía {ye('AS-REQ')}: usuario + marca de tiempo cifrada con tu contraseña"),
            (3.4, f"El KDC responde con el {pk('TGT')}, firmado con la clave de {rd('krbtgt')}")],
            items=[dict(type='graph', nodes=base(), edges=FAINT,
                packets=[dict(a='pc', b='kdc', t0=1.0, t1=2.3, label="AS-REQ", col=YELLOW, curve=-80, icon='lock'),
                         dict(a='kdc', b='pc', t0=3.4, t1=4.7, label="AS-REP · TGT", col=PINK, curve=-80, icon='ticket', hold=0.8)],
                badges=[dict(node='kdc', kind='key', t=3.3)],
                chips=[dict(t=5.2, x=430, y=530, text="krbtgt: la cuenta que firma todos los TGT", col=hx('9D174D'), size=24, icon='key')])]),
        dict(title="2 · Pides el ticket de servicio", dur=9, captions=[
            (0, f"Con el TGT pides acceso a un servicio concreto: su {cy('SPN')}"),
            (3.4, f"El ticket va cifrado con la {ye('clave de la cuenta del servicio')}")],
            items=[dict(type='graph', nodes=base(), edges=FAINT,
                packets=[dict(a='pc', b='kdc', t0=0.9, t1=2.2, label="TGS-REQ + TGT", col=YELLOW, curve=-80, icon='ticket'),
                         dict(a='kdc', b='pc', t0=3.4, t1=4.7, label="Ticket de servicio", col=CYAN, curve=-80, icon='ticket', hold=0.8)],
                chips=[dict(t=5.2, x=430, y=530, text="Cifrado con la clave de la cuenta del servicio", col=hx('155E75'), size=24, icon='lock')])]),
        dict(title="3 · Accedes al servicio", dur=8, captions=[
            (0, f"Presentas el ticket al servidor con {cy('AP-REQ')}"),
            (4.0, f"Tu contraseña {gr('nunca viaja')} por la red")],
            items=[dict(type='graph', nodes=base(), edges=FAINT,
                packets=[dict(a='pc', b='srv', t0=0.8, t1=2.0, label="AP-REQ + ticket", col=CYAN, curve=-70, icon='ticket'),
                         dict(a='srv', b='pc', t0=2.9, t1=4.0, label="Acceso concedido", col=GREEN, curve=-70, icon='check', hold=0.8)],
                badges=[dict(node='srv', kind='check', t=2.2)],
                chips=[dict(t=4.2, x=430, y=530, text="Sin contraseña en la red", col=hx('065F46'), size=26, icon='shield')])]),
        dict(title="Las joyas de la corona", dur=9, captions=[
            (0, f"Entender Kerberos = {ye('entender los ataques a AD')}"),
            (4.6, f"Los veremos a fondo en el {pk('episodio 5')}")],
            items=[dict(type='cards', y=500, h=230, gap=26, items=[
                dict(t=0.3, icon='key', col=RED, title="krbtgt", desc=f"Su clave firma todos los TGT. Si la roban: {rd('Golden Ticket')}"),
                dict(t=1.4, icon='server', col=ORANGE, title="Cuentas de servicio (SPN)", desc=f"Su clave cifra los tickets. Si es débil: {rd('Kerberoasting')}"),
                dict(t=2.5, icon='clock', col=CYAN, title="La hora importa", desc="Más de 5 min de desfase con el DC y Kerberos falla")])]),
        dict(title="¿Y NTLM?", dur=8.5, captions=[
            (0, f"{ye('NTLM')} sigue vivo por compatibilidad"),
            (4.3, f"Objetivo: {cy('auditar su uso')} y reducirlo al mínimo")],
            items=[dict(type='compare', y=520, t=0.2,
                        left=("NTLM", ORANGE, [(0.7, "Heredado: desafío-respuesta"), (1.3, "Vulnerable a relay y pass-the-hash"), (1.9, "Sin autenticación mutua")], 'x'),
                        right=("KERBEROS", GREEN, [(2.6, "Tickets con caducidad"), (3.2, "Autenticación mutua"), (3.8, "Cifrado AES")], 'check'))]),
    ],
    recap=[("TGT = tu pulsera", "Lo emite el KDC tras validar tu contraseña"),
           ("Ticket de servicio = tu entrada", "Uno por cada servicio (SPN)"),
           ("krbtgt firma todos los TGT", "Protegerla es crítico"),
           ("NTLM = legado", "Audítalo y redúcelo")],
    next=("SIGUIENTE · EP. 03", "Auditoría básica de AD"),
)
